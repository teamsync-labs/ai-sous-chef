## Как повторить eval

### 1. Подготовка
```bash
cd prompts/
pip install jinja2 pyyaml

## Прогон всех кейсов
python eval/run_eval.py --all --version v2 --type recipes_with_normalize

## Прогон конкретного кейса
python eval/run_eval.py --case 3 --version v2 --type normalize_products

## 