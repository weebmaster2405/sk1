# Deployment Checklist

## Pre-deployment Steps
1. [ ] Ensure all code is committed and pushed to GitHub
2. [ ] Test all features locally
3. [ ] Check all environment variables are documented
4. [ ] Run tests if available
5. [ ] Collect and compress static files

## PythonAnywhere Setup
1. [ ] Create PostgreSQL database
   - Database name: aniket3077$default
   - Username: aniket3077
   - Note down password

2. [ ] Clone repository
   ```bash
   cd ~
   git clone https://github.com/weebmaster2405/sk1.git insideorgs
   cd insideorgs
   ```

3. [ ] Set up virtual environment
   ```bash
   python3.9 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. [ ] Configure Web App
   - [ ] Create new web app
   - [ ] Choose Python 3.9
   - [ ] Set source code: /home/aniket3077/insideorgs
   - [ ] Set working directory: /home/aniket3077/insideorgs
   - [ ] Set virtual environment: /home/aniket3077/insideorgs/venv

5. [ ] Set Environment Variables
   ```
   DJANGO_SETTINGS_MODULE=orgchart.settings_production
   SECRET_KEY=<generate_new_secret_key>
   DB_PASSWORD=<your_postgres_password>
   EMAIL_HOST_USER=<your_email>
   EMAIL_HOST_PASSWORD=<your_email_app_password>
   ```

6. [ ] Configure Static Files
   - [ ] URL: /static/
   - [ ] Directory: /home/aniket3077/insideorgs/staticfiles
   - [ ] URL: /media/
   - [ ] Directory: /home/aniket3077/insideorgs/media

7. [ ] Run Migrations
   ```bash
   python manage.py migrate
   ```

8. [ ] Collect Static Files
   ```bash
   python manage.py collectstatic --noinput
   ```

9. [ ] Create Superuser
   ```bash
   python manage.py createsuperuser
   ```

## Post-deployment Checks
1. [ ] Test admin login
2. [ ] Test user registration
3. [ ] Test file uploads
4. [ ] Test payment integration
5. [ ] Test email functionality
6. [ ] Monitor error logs
7. [ ] Check static files are served correctly
8. [ ] Test all CRUD operations

## Security Checks
1. [ ] DEBUG is set to False
2. [ ] SECRET_KEY is secure and not in code
3. [ ] ALLOWED_HOSTS is properly configured
4. [ ] Database credentials are secure
5. [ ] SSL/HTTPS is enforced
6. [ ] CORS settings are correct
7. [ ] CSRF protection is enabled

## Maintenance
1. [ ] Set up regular database backups
2. [ ] Configure error logging
3. [ ] Set up monitoring
4. [ ] Document deployment process
5. [ ] Keep deployment script updated 