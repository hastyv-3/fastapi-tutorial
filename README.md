# FastAPI User Management and JWT Auth API
A RESTful API built with FastAPI, SQLAlchemy, and SQLite. Supports user registration and authorization via OAuth2 with password login and JWT Token.
## Endpoints
- **GET**
    - /
    - /profile
    - /verify-token
    - /users
    - /users/search
    - /users/{user_id}
- **POST**
    - /register
    - /token
    - /users
- **PUT**
    - /users/{user_id}
- **DELETE**
    - /users/{user_id}
## Stack
- **Framework:** FastAPI, Uvicorn
- **Database:** SQLAlchemy, SQLite
- **Validation:** Pydantic
- **Security:** bcrypt, PyJWT
## Modifications
#### [SQLAlchemy documentation on mapped_column() usage](https://docs.sqlalchemy.org/en/21/orm/declarative_tables.html#declarative-table-with-mapped-column)
Defining table attributes with `Column()` caused Pylance type errors when passing argument with the dot operator (inferring `Column[str]` instead of `str`). Bracket notation is not possible since SQLAlchemy returns ORM objects not subscriptable dicts. Replacing `Column()` with `mapped_column()` and `Mapped[]` type hints resolved Pylance issues with the dot operator along with being the SQLAlchemy recommended way for versions 2.0+.
#### [Passlib ValueError bug with bcrypt](https://github.com/pyca/bcrypt/issues/1079#issuecomment-3355164103)
Beginning with `bcrypt==5.0.0`, using bcrypt via passlib's `CryptContext(schemes=["bcrypt"], deprecated="auto")` causes a `ValueError: password cannot be longer than 72 bytes` regardless of password length. Since passlib has been unmaintained for over 6 years (as of writing), it was removed in favor of directly using `bcrypt.hashpw()` and `bcrypt.checkpw()`.
## Setup and Installation
1. **Clone repository**
```
git clone https://github.com/hastyv-3/fastapi-tutorial
cd fastapi-tutorial
```
2. **Create virtual environment**
```
python -m venv venv
venv\Scripts\activate
```
3. **Install dependencies**
```
pip install -r requirements.txt
```
4. **Start development server**
```
uvicorn myapi:app --reload
```
5. **Explore API**\
Open `http://127.0.0.1:8000/docs`
## Acknowledgements
Adapted from [FastAPI Crash Course by Code with Josh](https://www.youtube.com/playlist?list=PLEpRcxOmTFlOy8CjuwQ0CGJp1fTCgQcHB)