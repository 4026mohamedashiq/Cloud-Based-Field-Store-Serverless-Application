 Serverless Event-Driven Sports Analytics Backend

A fully serverless, event-driven sports analytics backend built using AWS services.

The project automatically calculates and updates team statistics whenever new player data is entered. It uses an event-driven architecture, so the system reacts to database changes in real time instead of relying on polling or scheduled jobs.

---

📌 Project Objective

The main objective of this project is to build a **real-time sports analytics backend** that automatically processes player data and updates team statistics whenever new data is added.

The architecture is:

- Serverless
- Event-driven
- Scalable
- Secure
- Observable
- Infrastructure-as-Code based

---

 🏗️ Architecture

The project uses the following AWS services:

| AWS Service | Purpose |
|---|---|
| Amazon S3 | Frontend hosting |
| AWS WAF | Web application security |
| Amazon DynamoDB | Database |
| DynamoDB Streams | Captures database changes |
| AWS Lambda | Event-driven processing |
| Amazon CloudWatch | Monitoring and logging |
| Amazon SNS | Notifications and alerts |
| AWS CloudFormation | Infrastructure as Code |

---

 🔄 How the Project Works

The complete flow of the application is:

```text
Manager
   |
   v
AWS WAF
   |
   v
Amazon S3
   |
   v
Amazon DynamoDB
   |
   v
DynamoDB Streams
   |
   v
AWS Lambda
   |
   v
Team Statistics
   |
   +------> CloudWatch
   |
   +------> SNS Alerts