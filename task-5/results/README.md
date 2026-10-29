
# Задача #

Представить проект по мониторингу/логированию/оповещению, на котором отобразить ключевые метрики, данные для логов и диаграмму с архитектурой решения.

# Решение #

## ADR файлы решения ##

**ADR задачи мониторинга**
`ADR-05-1.md`

**ADR задачи генерации алертов**
`ADR-05-2.md`

## Диаграмма решения ##
![](./final-state-with-observability.png)

## Скриншоты реализованного решения ##

### Метрики в Prometheus ###
![](./screenshots/prometheus-1.png)
![](./screenshots/prometheus-2.png)

### Метрики в Grafana ###
![](./screenshots/grafana.png)

### Алерты в Alert Manager ###
![](./screenshots/job-failed-alertmanager.png)

### Алерты в почте ###
![](./screenshots/job-failed-mailhog1.png)
![](./screenshots/job-failed-mailhog2.png)

### Логи в Kibana ###
![](./screenshots/kibana-batch-processing.png)
![](./screenshots/kibana-error-details.png)
