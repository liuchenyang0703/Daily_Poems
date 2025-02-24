@echo off

cd C:\Users\user\Desktop\定时推送\Daily_Poems

REM Retrieve daily poetry to index.html
curl https://v1.jinrishici.com/all.txt > ./index.html

REM Add files to the staging area
git add .

REM Commit changes to the local repository
git commit -m "Daily poetry"

REM Push changes to the remote repository
git push https://github.com/liuchenyang0703/Daily_Poems.git

REM Display completion message
echo Commit completed!

REM Pause to wait for user input before closing the command prompt
pause