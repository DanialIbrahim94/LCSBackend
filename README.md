# LCS Backend
Automated Digital Delivery System - BusinessTRAK

# Python Version
3.10.2

## How to run locally (Windows version)
### Steps:
- Clone the project and navigate to it:
```
git clone https://github.com/DanialIbrahim94/LCSBackend
cd LCSBackend
```
- install, create and activate a new virtual environment
```
 pip install virtualenv
 virtualenv venv
 venv\Scripts\activate.bat
```
- install all dependencies
```
pip install -r requirements.txt
```
- create a new file named `.env` and fill it with(You can generate a new SECRET_KEY online):
```
SECRET_KEY=django-insecure-f6$pktd!w($q)83)8+u(ze+9mbom(a6pwkva)5vkem94cv2p0$
ALLOWED_HOSTS=.localhost:3000, .127.0.0.1
```
- run migration command(Note that we are using SQLite for development):
```
python manage.py migrate
```
- create the superuse/admin using the custom command 'create-admin-user':
```
python manage.py create-admin-user
```
- run the project
```
python manage.py runserver
```

## Check if the project is working probably:
Navigate to this link: `http://127.0.0.1:8000/users/list/` and you should see a JSON format of the superuser you just created
