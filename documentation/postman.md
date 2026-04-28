Registering a new user: 
http://127.0.0.1:8000/api/v1/register

Raw JSON body: 
{
  "name": "admin2",
  "email": "admin2@admin.com",
  "password": "admin2",
  "role": "admin"
}


---



User Login: 
http://127.0.0.1:8000/api/v1/register

x-www-form-urlencoded

    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbkB0ZXN0LmNvbSIsImV4cCI6MTc3NzMwMjQ1NH0.q5_IbTrjQX1oIf0Xy6vUI5Q2yf4lK3CnohE4oBpwezo",
    eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbkB0ZXN0LmNvbSIsImV4cCI6MTc3NzMwOTcyNn0.roR-KqnSgC3KHq4x4e25FM33Ffbr7kTGs-QOisoix54


USERS: 
1. GET all Users - Admin Only
2. GET Specific User - Admin Only
3. Create New User - Admin Only

4. Get information about current user
