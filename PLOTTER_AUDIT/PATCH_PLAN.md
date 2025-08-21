# План правок для поддержки нескольких плоттеров

## Вариант 1: пул экземпляров в одном процессе
1. **Graphtec.SilhouetteCameo**
   - добавить параметр `selector` (bus/addr или serial);
   - использовать `usb.core.find(custom_match=...)` для открытия нужного устройства;
   - хранить `selector` в `self.selector` и выводить в логи.
2. **plotter_manager.py**
   - `find_plotters` дополнить возвратом `bus` и `address`/serial;
   - реализовать `get_plotter(selector)` → создаёт/кэширует `SilhouetteCameo` и возвращает lock.
3. **sendto_silhouette.py**
   - принимать `--device`/`selector` и передавать в `SilhouetteCameo`.
4. Добавить простую очередь заданий на уровне `PlotterManager`, чтобы последовательно обслуживать job на каждый `selector`.

## Вариант 2: отдельный процесс на устройство
1. Создать модуль `device_worker.py`, который:
   - запускает `SilhouetteCameo(selector)` в отдельном процессе;
   - читает команды из `multiprocessing.Queue` и выполняет `plot`.
2. **PlotterRouter** в основном процессе:
   - обнаруживает устройства, поднимает процессы и держит очереди;
   - распределяет job и следит за timeouts/перезапуском.
3. Обновить `sendto_silhouette.py` для отправки задания через роутер.
4. Добавить IPC‑протокол для передачи прогресса и ошибок.

## Общие изменения
* Обновить тесты (`test_plotter_manager.py`) для выбора устройств по `selector`.
* Обновить документацию и примеры (`PLOTTER_AUDIT/SCRIPTS/send_to_two.py`).

