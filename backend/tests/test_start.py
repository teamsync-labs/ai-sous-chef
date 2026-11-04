"""
Тесты хендлеров backend/bot/handlers/start.py.

Покрываем FSM из двух согласий:
  /start              → waiting_for_accept_first_consent
  «Согласен» (privacy) → waiting_for_accept_second_consent
  «Согласен» (pdn)     → state=None, data={"is_accept_consents": True}

Реальные TG API и Consent API не используются — только моки.
"""

from handlers.start import (
    on_first_consent_callback,
    on_second_consent_callback,
    start_cmd,
)
from states.accept_states import AcceptConsent


# ───────────────────────────── /start ─────────────────────────────


async def test_start_sets_waiting_for_first_consent(
    state, make_message, mock_record_consent
):
    """После /start FSM ждёт первое согласие (privacy)."""
    await start_cmd(make_message("/start"), state)

    assert (
        await state.get_state()
        == AcceptConsent.waiting_for_accept_first_consent.state
    )
    mock_record_consent.assert_not_awaited()


async def test_start_sends_first_consent_message(
    state, make_message, mock_record_consent
):
    """После /start пользователю отправляется первое сообщение с кнопками."""
    msg = make_message("/start")
    await start_cmd(msg, state)

    msg.answer.assert_awaited_once()
    mock_record_consent.assert_not_awaited()


async def test_start_when_already_accepted_does_not_touch_state(
    state, make_message, mock_record_consent
):
    """Если оба согласия уже даны — /start не сбрасывает state и не пишет consent."""
    await state.set_state(None)
    await state.set_data({"is_accept_consents": True})
    msg = make_message("/start")

    await start_cmd(msg, state)

    assert await state.get_state() is None
    assert (await state.get_data())["is_accept_consents"] is True
    msg.reply.assert_awaited_once()
    mock_record_consent.assert_not_awaited()


async def test_start_on_second_stage_keeps_state(
    state, make_message, mock_record_consent
):
    """
    Повторный /start, когда первое согласие уже дано, не откатывает
    пользователя на первый этап (требование ТЗ: «остаётся прошлое состояние»).
    """
    await state.set_state(AcceptConsent.waiting_for_accept_second_consent)
    await state.set_data({"is_accept_first_consent": True})
    msg = make_message("/start")

    await start_cmd(msg, state)

    assert (
        await state.get_state()
        == AcceptConsent.waiting_for_accept_second_consent.state
    )
    mock_record_consent.assert_not_awaited()


# ────────────────── отправка «любого другого сообщения» ──────────────────


async def test_any_other_message_keeps_state_and_no_record(
    state, mock_record_consent
):
    """
    Левое сообщение не попадает в хендлер /start (фильтр CommandStart),
    поэтому state не меняется и record_consent не зовётся.
    """
    await state.set_state(AcceptConsent.waiting_for_accept_first_consent)

    from aiogram.filters import CommandStart

    from handlers.start import start_cmd as _start_cmd

    # Проверяем, что фильтр /start не пропускает произвольный текст.
    assert not (await CommandStart()(_make_event("hello"), None))
    mock_record_consent.assert_not_awaited()
    assert (
        await state.get_state()
        == AcceptConsent.waiting_for_accept_first_consent.state
    )


def _make_event(text: str):
    """Минимальный фейковый Message для проверки фильтра CommandStart."""
    from unittest.mock import MagicMock

    msg = MagicMock()
    msg.text = text
    return msg


# ────────────────────── первое согласие (privacy) ──────────────────────


async def test_first_consent_granted_moves_to_second_state(
    state, make_callback, callback_data, mock_record_consent
):
    """Первое «Согласен» пишет privacy/granted и ведёт ко второму этапу."""
    await state.set_state(AcceptConsent.waiting_for_accept_first_consent)
    cb = make_callback(question=1, consent=True)

    await on_first_consent_callback(
        cb, callback_data(question=1, consent=True), state
    )

    mock_record_consent.assert_awaited_once_with(
        external_id="42", consent_type="privacy", action="granted"
    )
    assert (
        await state.get_state()
        == AcceptConsent.waiting_for_accept_second_consent.state
    )
    assert (await state.get_data())["is_accept_first_consent"] is True


async def test_first_consent_declined_keeps_state_and_no_record(
    state, make_callback, callback_data, mock_record_consent
):
    """Отказ на первом этапе: state не меняется, consent не пишется."""
    await state.set_state(AcceptConsent.waiting_for_accept_first_consent)
    cb = make_callback(question=1, consent=False)

    await on_first_consent_callback(
        cb, callback_data(question=1, consent=False), state
    )

    mock_record_consent.assert_not_awaited()
    assert (
        await state.get_state()
        == AcceptConsent.waiting_for_accept_first_consent.state
    )


async def test_first_consent_declined_replaces_message(
    state, make_callback, callback_data, mock_record_consent
):
    """Отказ на первом этапе: старое сообщение удаляется и отправляется заново."""
    await state.set_state(AcceptConsent.waiting_for_accept_first_consent)
    cb = make_callback(question=1, consent=False)

    await on_first_consent_callback(
        cb, callback_data(question=1, consent=False), state
    )

    cb.message.delete.assert_awaited_once()
    cb.message.answer.assert_awaited_once()


# ────────────────────── второе согласие (pdn) ──────────────────────


async def test_second_consent_granted_clears_state_and_sets_flag(
    state, make_callback, callback_data, mock_record_consent
):
    """Второе «Согласен» пишет pdn/granted, ставит флаг и сбрасывает state."""
    await state.set_state(AcceptConsent.waiting_for_accept_second_consent)
    await state.set_data({"is_accept_first_consent": True})
    cb = make_callback(question=2, consent=True)

    await on_second_consent_callback(
        cb, callback_data(question=2, consent=True), state
    )

    mock_record_consent.assert_awaited_once_with(
        external_id="42", consent_type="pdn", action="granted"
    )
    assert await state.get_state() is None
    assert (await state.get_data()) == {"is_accept_consents": True}


async def test_second_consent_declined_keeps_state_and_no_record(
    state, make_callback, callback_data, mock_record_consent
):
    """Отказ на втором этапе: state не меняется, consent не пишется."""
    await state.set_state(AcceptConsent.waiting_for_accept_second_consent)
    await state.set_data({"is_accept_first_consent": True})
    cb = make_callback(question=2, consent=False)

    await on_second_consent_callback(
        cb, callback_data(question=2, consent=False), state
    )

    mock_record_consent.assert_not_awaited()
    assert (
        await state.get_state()
        == AcceptConsent.waiting_for_accept_second_consent.state
    )


async def test_second_consent_declined_replaces_message(
    state, make_callback, callback_data, mock_record_consent
):
    """Отказ на втором этапе: старое сообщение удаляется и отправляется заново."""
    await state.set_state(AcceptConsent.waiting_for_accept_second_consent)
    cb = make_callback(question=2, consent=False)

    await on_second_consent_callback(
        cb, callback_data(question=2, consent=False), state
    )

    cb.message.delete.assert_awaited_once()
    cb.message.answer.assert_awaited_once()


# ──────────────────────── полный happy-path ────────────────────────


async def test_full_consent_flow_calls_record_twice_in_order(
    state, make_message, make_callback, callback_data, mock_record_consent
):
    """Полный проход: privacy → pdn, record_consent зовётся дважды в правильном порядке."""
    await start_cmd(make_message("/start"), state)

    await on_first_consent_callback(
        make_callback(question=1, consent=True),
        callback_data(question=1, consent=True),
        state,
    )
    await on_second_consent_callback(
        make_callback(question=2, consent=True),
        callback_data(question=2, consent=True),
        state,
    )

    assert mock_record_consent.await_count == 2
    calls = mock_record_consent.await_args_list
    assert calls[0].kwargs["consent_type"] == "privacy"
    assert calls[1].kwargs["consent_type"] == "pdn"
    assert await state.get_state() is None
    assert (await state.get_data()) == {"is_accept_consents": True}