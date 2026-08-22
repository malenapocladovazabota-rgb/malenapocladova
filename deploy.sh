#!/bin/bash
# Деплой сайта на Cloudflare Pages через GitHub.
# Запуск из Терминала:
#   cd "/Users/levpocladov/Desktop/Claude/Claude Cowork/SMM с нуля/course-site" && bash deploy.sh
#
# Можно передать своё сообщение коммита:
#   bash deploy.sh "поправил цену на лендинге"

set -e
cd "$(dirname "$0")"

MSG="${1:-site}"

# пересобрать версию для правок, если менялся лендинг
if [ -f build-review.py ]; then
  python3 build-review.py
fi

git add -A

if git diff --cached --quiet; then
  # Правок нет. Но коммит мог быть сделан раньше и не уехать:
  # например, его сделали там, где нет доступа к GitHub. Проверяем и досылаем.
  if [ -n "$(git log origin/main..HEAD --oneline 2>/dev/null)" ]; then
    echo "Новых правок нет, но есть неотправленные коммиты. Отправляю."
    git push origin main
    echo
    echo "Отправлено. Cloudflare Pages соберёт сайт за 1-2 минуты."
    exit 0
  fi
  echo "Изменений нет, деплоить нечего."
  exit 0
fi

git commit -m "$MSG"
git push origin main

echo
echo "Отправлено. Cloudflare Pages соберёт сайт за 1–2 минуты."
echo "  Лендинг:        https://malenapocladova.com/prodvizhenie"
echo "  Версия правок:  https://malenapocladova.com/prodvizhenie-review"
echo "  Пароль:         prodvijenie2026"
