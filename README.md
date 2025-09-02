# Flask DevOps Portfolio

A containerized Flask web application with PostgreSQL, Docker Compose, and Flask-Migrate — built as part of a DevOps learning and portfolio project.

---

## 🚀 Quick Start

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd FlaskProject
```

### 2. Setup environment
Copy example file:
```bash
cp .env.example .env
```

### 3. Run with Docker Compose
```bash
make containers-up
```

### 4. Access the app
Open [http://localhost:5000](http://localhost:5000)

---

## 🛠️ Common Commands

- Start containers:  
  ```bash
  make containers-up
  ```

- Stop containers:  
  ```bash
  make containers-down
  ```

- Run DB migrations:  
  ```bash
  make db-migrate-up
  ```

- Open Postgres shell:  
  ```bash
  make db-shell
  ```

---

## 📄 Documentation

- 📌 [Project Snapshot](https://github.com/karanbsk/FlaskProject/blob/main/PROJECT_SNAPSHOT.md) — structure & workflow summary  
- 📖 [Project Documentation](https://github.com/karanbsk/FlaskProject/blob/main/docs/project_documentation.md) — detailed explanations, enhancements, future plans  

---

## 🤝 Contributing
Pull requests are welcome! For significant changes, please open an issue first.

---

## 📜 License
[MIT](LICENSE)
