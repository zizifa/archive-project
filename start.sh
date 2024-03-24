cd /home/zizi/archive-project
rm result.log
touch result.log
venv/bin/pip install -r requirements.txt
venv/bin/python main.py > result.log
echo "RESULT LOGS SAVED IN result.log FILE IN THIS DIRECTORY. GOOD LUCK"
