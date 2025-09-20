# Flask DevOps Portfolio: Containerized Application with CI/CD & Kubernetes Integration

**Author:** Karan  
**Date:** 31-08-2025  
**Version:** 1.1  

---

## Table of Contents
1. Executive Summary  
2. Purpose of the Project  
3. Objective of the Project  
4. Project Overview  
5. Tools and Technologies  
6. Project Implementation Details  
7. Versioning and Milestones  
8. Change Log: v1.1  
9. Achievements, Current Progress, and Future Enhancements  
10. Project Status  
11. Future Roadmap  
12. Mermaid Diagrams  
13. Appendices / References

---

## Executive Summary
This project demonstrates a professional-grade DevOps workflow for a Flask-based application, integrating environment-based configuration, containerization, database management, CI/CD automation, and preparation for Kubernetes deployment. The documentation provides a clear overview, versioning history, and a roadmap for future enhancements.

---

## Purpose of the Project
The purpose of this project is to create a fully documented, containerized Flask application that showcases modern DevOps practices and is ready for demonstration, testing, and GitHub repository presentation.

---

## Objective of the Project
1. Develop a Flask application following modern development best practices.  
2. Integrate a Postgres database with proper migrations.  
3. Implement environment-specific configuration management.  
4. Containerize the application and database using Docker.  
5. Demonstrate CI/CD pipeline automation with GitHub Actions.  
6. Prepare the application for Kubernetes deployment.  
7. Maintain professional documentation suitable for GitHub and demos.

---

## Project Overview
**Architecture:**  

**Development Environment:**  
- Flask App Container + Postgres DB Container  
- Database initialization script (`create_db.py`) to quickly create the database schema locally using SQLAlchemy models.  
  - Usage: `python create_db.py`  
  - Respects environment configuration (development, testing) via `config.py`  

**Production Environment (Planned):**  
- Flask App Container + Database managed by AWS RDS / Managed Service  

**Database Strategy Across Environments**  

1. Development Environment (Dev)  
    - Full integration of FlaskApp + Postgres DB in local Docker containers.  
    - Tables are created, sample data inserted, and all CRUD APIs tested successfully.  
    - Confirms that the application works seamlessly with Postgres.  

2. Continuous Integration (CI) Workflows  
    - SQLite (in-memory or file-based) is used instead of Postgres.  
        - Purpose:  
            - Fast and isolated testing of Flask app logic and routes.  
            - Snapshot generation and unit tests can run without spinning up a full Postgres instance.  
            - Ensures CI is lightweight and repeatable.  
        - Impact:  
            - CI tests do not validate Postgres-specific behaviors.  
            - Production and Dev integrations remain unaffected.  

3. Production Environment (Prod)  
    - Managed Postgres DB via AWS RDS or equivalent.  
    - Since Dev already validated FlaskApp integration with Postgres, risk of issues in Prod is minimal.  
    - Deployment involves connecting the FlaskApp container to the managed DB—no code changes needed.  

4. Best Practices & Justification  
    - Using a different DB in CI is safe because CI is focused on code correctness, not DB-specific behavior.  
    - Postgres validation is guaranteed in Dev and replicated in Prod.  
    - Ensures fast CI pipelines, minimal infrastructure overhead, and safe deployments.  

---

## Tools and Technologies
| Category | Tool/Technology | Purpose |
|----------|----------------|---------|
| Backend | Python 3.11, Flask | Application development |
| Database | Postgres, Alembic | Database management & migrations |
| Containerization | Docker, docker-compose | Dev & prod environment setup |
| CI/CD | GitHub Actions | Pipeline automation (push to GHCR, deploy) |
| Cloud / Future | AWS RDS, EC2, S3 | Production-ready services |
| Infrastructure as Code | Terraform | Planned automation |
| Monitoring | Grafana, Prometheus | Planned observability |
| Frontend | HTML, CSS, Jinja | Templates & UI rendering |

---

## Project Implementation Details
**Folder Structure:**  
```
FlaskProject/
├── app/
│   ├── __init__.py
│   ├── routes.py
│   ├── config.py
├── migrations/
├── Dockerfile
├── docker-compose.dev_db.yml
├── .env
├── wsgi.py
```

**Key Points:**  
- Models (models.py) created  
- Flask container build validation completed  
- DB container persistent volume already running  
- Hot reload & curl API testing verified  

---

## Versioning and Milestones
> Version 1.0 reflects the initial finalized state of the Flask DevOps Portfolio as of 30-08-2025.

| Date (DD-MM-YYYY) | Feature / Milestone | Tools/Techniques | Status |
|------------------|------------------|-----------------|--------|
| 06-08-2025 | Flask project setup & basic app | Flask, Python | Completed |
| 08-08-2025 | Environment configuration | .env, config.py | Completed |
| 28-08-2025 | Dockerfile for Flask App | Docker | Completed |
| 29-08-2025 | Docker-compose dev DB setup | Docker Compose, Postgres | Completed |
| 30-08-2025 | Hot reload, curl API testing | Flask debug, curl | Completed |
| Future | Kubernetes, AWS, Terraform, Grafana, Prometheus | Planned | Planned |

---

## Change Log: v1.1
**Date:** 31-08-2025  
**Version:** 1.1  
**Changes since v1.0:**  

| Feature / Update | Description | Status |
|-----------------|-------------|--------|
| User Interface (UI) | Full CRUD implemented on `ui.html` page with modals for create/edit and action buttons for delete | Completed |
| Password Security | User passwords now hashed using `werkzeug.security.generate_password_hash` before storage in Postgres | Completed |
| Flash Messages | Success/failure notifications implemented using Flask `flash()` in `base.html` | Completed |
| Dashboard Improvements | Server time updated to use `Asia/Kolkata` timezone; database status reliably reported | Completed |
| Styling Enhancements | Center-aligned headings and content boxes on `index.html`; improved visual layout for modals and tables | Completed |
| Database Verification | Tables confirmed with Alembic migrations; sample data verified | Completed |
| Code Cleanup | Duplicate/unused routes removed; all routes correctly mapped to templates | Completed |

**Notes:**  
- This version is production-ready for demo and portfolio purposes.  
- v1.0 remains as a historical reference for development milestones.  

---

## Achievements, Current Progress, and Future Enhancements
**Achievements:**  
- Flask app development completed  
- DB integration & migration folders created  
- Dockerized DB container with persistent volume  
- Environment management centralized via config.py  
- Full CRUD with password hashing and flash messages implemented  

**Current Progress:**  
- Flask containerization completed  
- UI layer validated  
- CI/CD pipeline planning in progress  

**Future Enhancements:**  
- Kubernetes deployment & scaling  
- CI/CD automation with testing & deployment pipelines (push images to GHCR)  
- Monitoring & observability: Grafana, Prometheus  
- Infrastructure automation via Terraform  

---

## Project Status
**Summary Paragraph:**  
> Project is now fully functional. Core Flask app development, database integration, CRUD UI, and basic Dockerization are complete. Next steps include full CI/CD implementation, Kubernetes readiness, and monitoring setup. Documentation is updated for professional presentation and GitHub repository showcase.

**Tabular Status Summary:**
| Component | Status | Notes / Next Steps |
|-----------|--------|------------------|
| Flask App | Developed | Containerization completed |
| Database | Integrated & verified | Password hashing added |
| Dockerization | DB & App container completed | Production-ready container image validation pending |
| CI/CD | Planning stage | GitHub Actions setup upcoming |
| Future Enhancements | Planned | Kubernetes, AWS, Terraform, Grafana, Prometheus |

---

## Future Roadmap
- Kubernetes pod deployment & scaling  
- AWS-managed services (RDS, EC2, S3 deployment)  
- CI/CD automation & testing (push Docker images to GHCR)  
- Monitoring & observability: Grafana, Prometheus  
- Infrastructure as Code: Terraform  
- Continuous documentation updates as new tools/features are added  

---

## Appendices / References
### Code Files

[Dockerfile](https://github.com/karanbsk/FlaskProject/blob/main/Dockerfile)

[docker-compose.dev_db.yml](https://github.com/karanbsk/FlaskProject/blob/main/docker-compose.dev_db.yml)

[config.py](https://github.com/karanbsk/FlaskProject/blob/main/config.py)

### Diagrams

[Architecture Diagram](https://github.com/karanbsk/FlaskProject/blob/main/docs/diagrams/architecture.png)

[Docker & Container Flow](https://github.com/karanbsk/FlaskProject/blob/main/docs/diagrams/docker_flow.png)

[Database Flow](https://github.com/karanbsk/FlaskProject/blob/main/docs/diagrams/db_flow.png)

[CI/CD Flow](https://github.com/karanbsk/FlaskProject/blob/main/docs/diagrams/cicd_flow.png)

[Future Roadmap / Monitoring](https://github.com/karanbsk/FlaskProject/blob/main/docs/diagrams/monitoring_flow.png)

External References

[Flask Documentation](https://flask.palletsprojects.com/)

[Docker Documentation](https://docs.docker.com/)

[Postgres Documentation](https://www.postgresql.org/docs/)
