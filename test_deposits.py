#!/usr/bin/env python3

from tools.deposit_parser import get_best_deposits
import traceback

try:
    result = get_best_deposits()
    print('Результат:', result[:2] if result else 'Пустой результат')
    print('Количество вкладов:', len(result) if result else 0)
except Exception as e:
    print('Ошибка:', e)
    traceback.print_exc() 