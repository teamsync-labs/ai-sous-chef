## 1. Подготовка
```bash
cd prompts/
pip install jinja2 pyyaml

2. Прогон всех кейсов
python eval/run_eval.py --all --version v2 --type recipes_with_normalize

3. Прогон конкретного кейса
python eval/run_eval.py --case 3 --version v2 --type normalize_products

