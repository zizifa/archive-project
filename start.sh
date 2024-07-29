rm result.log
touch result.log
source venv/bin/activate
pip install -r requirements.txt
python main.py > result.log
echo "RESULT LOGS SAVED IN result.log FILE IN THIS DIRECTORY. GOOD LUCK"
