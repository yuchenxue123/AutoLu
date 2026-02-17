APP_NAME="LiveRecorder"

pyinstaller --noconfirm --onefile --windowed \
  --name "$APP_NAME" \
  "main.py"

mkdir -p "output"
mv dist/$APP_NAME.exe output/

rm -rf build dist
rm -rf $APP_NAME.exe