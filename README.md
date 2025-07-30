# sanusi

Install dependencies:

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

Frontend setup:

```bash
npm init -y
npm i webpack webpack-cli --save-dev
npm i @babel/core babel-loader @babel/preset-env @babel/preset-react --save-dev
npm i react react-dom
npm install @mui/material @emotion/react @emotion/styled
npm install @mui/icons-material
npm i @babel/plugin-proposal-class-properties
npm i react-router-dom
```

Configure `webpack.config.js`, `babel.config.json`, and edit `package.json` as needed.

Run database migrations:

```bash
python manage.py migrate_schemas --shared
```

**WARNING:** Never use `migrate` as it would sync all your apps to `public`!

Use Ruff for linting:

```bash
ruff check .
ruff format .
```


for information on autogen, read this
```bash
medium.com/@shravankoninti/autogen-an-agentic-open-source-framework-for-intelligent-automation-d1c374c46bbb
```