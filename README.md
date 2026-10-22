# ⚽ FC Cloud Manager — Serverless Event-Driven Sports Analytics Backend

[![AWS Lambda](https://img.shields.io/badge/AWS-Lambda-FF9900?logo=awslambda&logoColor=white)](https://aws.amazon.com/lambda/)
[![Amazon DynamoDB](https://img.shields.io/badge/Amazon-DynamoDB-4053D6?logo=amazondynamodb&logoColor=white)](https://aws.amazon.com/dynamodb/)
[![Amazon API Gateway](https://img.shields.io/badge/Amazon-API%20Gateway-FF4F8B?logo=amazonapigateway&logoColor=white)](https://aws.amazon.com/api-gateway/)
[![Python](https://img.shields.io/badge/Python-3.9%20%7C%203.10%20%7C%203.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A high-performance, fully serverless, event-driven sports management and analytics backend built on **Amazon Web Services (AWS)**. The platform powers the **FC Cloud Rovers** football operations portal, automating squad roster management, match schedules, real-time injury tracking, and event-driven squad statistics recalculation.

---

## 📌 Project Objective

The primary objective is to deliver a **production-grade, real-time sports analytics backend** that automatically processes player events, updates club statistics in real-time, and triggers instant alerts without polling or scheduled cron jobs.

### Key Architectural Pillars:
- **Serverless & Scalable:** Zero server management with on-demand scaling via AWS Lambda and Amazon DynamoDB.
- **Event-Driven:** Reactive processing using DynamoDB Streams to detect roster modifications and health status updates.
- **Low Latency & High Availability:** Distributed multi-AZ resilience in the AWS Sydney (`ap-southeast-2`) region.
- **Secure by Design:** Protected by AWS WAF, CORS restriction, and least-privilege IAM execution roles.
- **Full Observability:** Comprehensive tracing, structured logging, and metric tracking via Amazon CloudWatch.

---

## 🏗️ Architecture & Data Flow

```
                                  +-------------------+
                                  |      Manager      |
                                  | (Web Browser UI)  |
                                  +---------+---------+
                                            |
                                            v
                                  +-------------------+
                                  |      AWS WAF      |
                                  +---------+---------+
                                            |
                     +----------------------+----------------------+
                     |                                             |
                     v                                             v
        +-------------------------+                   +-------------------------+
        |     Amazon S3 Bucket    |                   | Amazon API Gateway HTTP |
        | (Static Web Application)|                   |   (CORS Enabled / API)  |
        +-------------------------+                   +------------+------------+
                                                                   |
                                                                   v
                                                      +-------------------------+
                                                      |   AWS Lambda API Handler|
                                                      |  (`lambda_function.py`) |
                                                      +------------+------------+
                                                                   |
                                                                   v
                                                      +-------------------------+
                                                      |     Amazon DynamoDB     |
                                                      | ('players'/'FC_fixtures')
                                                      +------------+------------+
                                                                   |
                                                                   v
                                                      +-------------------------+
                                                      |    DynamoDB Streams     |
                                                      +------------+------------+
                                                                   |
                                                                   v
                                                      +-------------------------+
                                                      |   Stream Worker Lambda  |
                                                      | (`stream_processor.py`) |
                                                      +------------+------------+
                                                                   |
                                          +------------------------+------------------------+
                                          |                                                 |
                                          v                                                 v
                             +-------------------------+                       +-------------------------+
                             |    Amazon CloudWatch    |                       |       Amazon SNS        |
                             |   (Logs & Real-time     |                       |    (Medical / Squad     |
                             |       Dashboard)        |                       |      Email & SMS)       |
                             +-------------------------+                       +-------------------------+
```

### Flow Walkthrough:
1. **Frontend Request:** The manager accesses the portal hosted in an **Amazon S3** static website bucket protected by **AWS WAF**.
2. **API Interaction:** User actions (registering a player, checking fixtures) send asynchronous HTTPS requests to **Amazon API Gateway**.
3. **Lambda Execution:** The API routes requests to the `lambda_handler` in `lambda_function.py`, performing input sanitization, DynamoDB operations, and returning standardized CORS responses.
4. **Event Streaming:** Database write events on the `players` table trigger **DynamoDB Streams** in real time.
5. **Stream Processing & Alerts:** The stream triggers `stream_processor.py`, which identifies roster additions and injury flags, outputting structured logs to **Amazon CloudWatch** and broadcasting alerts through **Amazon SNS**.

---

## 🗂️ Project Structure

```bash
├── frontend.html          # FC Cloud Manager responsive web interface (HTML5/CSS3/Vanilla JS)
├── lambda_function.py     # Main AWS Lambda API router & CRUD handler (Python 3.x)
├── stream_processor.py    # Dedicated DynamoDB Streams event-driven processor (Python 3.x)
├── Backend code.txt       # Clean copy of backend handler script
└── README.md              # Project documentation, deployment guide, and API specification
```

---

## 🚀 AWS Services Overview

| AWS Service | Function & Purpose |
|---|---|
| **Amazon S3** | Hosts the static single-page application (`frontend.html`) with zero server overhead. |
| **AWS WAF** | Web Application Firewall protecting the frontend and APIs from web exploits and bots. |
| **Amazon API Gateway** | Provides HTTP endpoints (`/players`, `/fixtures`, `/stats`) with CORS handling. |
| **AWS Lambda** | Executes serverless business logic and processes streaming database records. |
| **Amazon DynamoDB** | Fully managed NoSQL key-value database storing player and fixture records. |
| **DynamoDB Streams** | Captures time-ordered sequence of item-level modifications on DynamoDB tables. |
| **Amazon CloudWatch** | Aggregates application logs, Lambda invocation metrics, and runtime errors. |
| **Amazon SNS** | Publishes instant notifications when medical alerts or squad changes occur. |

---

## 📡 API Specification & Endpoints

Base URL: `https://<api-id>.execute-api.<region>.amazonaws.com`

### 1. Squad Management (`/players`)

#### `GET /players`
Retrieves the complete first-team roster.
- **Response `200 OK`**:
```json
[
  {
    "playerId": "P101",
    "name": "Cristiano",
    "position": "Forward",
    "jerseyNumber": 7,
    "fitness": "100%"
  },
  {
    "playerId": "P102",
    "name": "Neymar",
    "position": "Forward",
    "jerseyNumber": 10,
    "fitness": "Injury (Ankle)"
  }
]
```

#### `POST /players`
Registers or updates a player record.
- **Request Body**:
```json
{
  "playerId": "P119",
  "name": "Lionel",
  "position": "Forward",
  "jerseyNumber": 10,
  "fitness": "100%"
}
```
- **Response `201 Created`**:
```json
{
  "message": "Player permanently saved to DynamoDB!",
  "item": {
    "playerId": "P119",
    "name": "Lionel",
    "position": "Forward",
    "jerseyNumber": 10,
    "fitness": "100%"
  }
}
```

#### `DELETE /players?playerId=P119`
Deletes a player from the squad.
- **Response `200 OK`**:
```json
{
  "message": "Player P119 deleted successfully."
}
```

---

### 2. Match Schedule (`/fixtures`)

#### `GET /fixtures`
Returns the club's season fixture list.
- **Response `200 OK`**:
```json
[
  {
    "fixtureId": "FIX_2026-08-15_Chelsea",
    "date": "2026-08-15",
    "venue": "Home",
    "opponent": "Chelsea FC",
    "competition": "Premier League",
    "result": "W 3-1"
  }
]
```

#### `POST /fixtures`
Creates a new fixture entry.
- **Request Body**:
```json
{
  "date": "2026-10-24",
  "venue": "Home",
  "opponent": "FC Barcelona",
  "competition": "Champions League",
  "result": "Upcoming"
}
```

---

### 3. Club Analytics (`/stats`)

#### `GET /stats`
Computes real-time squad statistics directly from DynamoDB.
- **Response `200 OK`**:
```json
{
  "squadSize": 18,
  "injuredCount": 1,
  "injuredPlayers": ["Neymar"],
  "positionsBreakdown": {
    "Forward": 9,
    "Midfielder": 2,
    "Defender": 6,
    "Goalkeeper": 1
  },
  "nextFixture": "vs Real Madrid (A)",
  "topScorer": "Cristiano (25)",
  "winRate": "85.0%"
}
```

---

## 🛠️ Step-by-Step Deployment Guide

### Step 1: Create Amazon DynamoDB Tables
1. Open the **AWS DynamoDB Console**.
2. Create the first table:
   - **Table name:** `players`
   - **Partition key:** `playerId` (String)
   - Enable **DynamoDB Streams** (`New and old images`).
3. Create the second table:
   - **Table name:** `FC_fixtures`
   - **Partition key:** `fixtureId` (String)

### Step 2: Configure IAM Role for Lambda
Create an execution role (e.g. `FCCloudManagerLambdaRole`) with permissions:
- `AWSLambdaBasicExecutionRole` (CloudWatch logging)
- `AmazonDynamoDBFullAccess` (or scoped Read/Write policy on `players` and `FC_fixtures`)
- `AmazonSNSFullAccess` (or `sns:Publish` on your alert topic)
- `AWSLambdaDynamoDBExecutionRole` (for stream ingestion)

### Step 3: Deploy AWS Lambda Function
1. Open the **AWS Lambda Console** and click **Create function**.
2. **Function name:** `FC_Cloud_Backend`
3. **Runtime:** Python 3.9+
4. **Execution role:** Attach `FCCloudManagerLambdaRole`.
5. Paste the code from [`lambda_function.py`](lambda_function.py) into the editor.
6. Under **Configuration > Environment variables**, configure:
   - `PLAYERS_TABLE`: `players`
   - `FIXTURES_TABLE`: `FC_fixtures`
   - `SNS_TOPIC_ARN`: *(Optional: your SNS ARN)*
7. Click **Deploy**.

### Step 4: Configure Amazon API Gateway (HTTP API)
1. In the **Amazon API Gateway Console**, create an **HTTP API**.
2. Set API name to `FC-Cloud-API`.
3. Add routes:
   - `ANY /players`
   - `ANY /fixtures`
   - `GET /stats`
   - `POST /login`
   - `OPTIONS /{proxy+}`
4. Attach the `FC_Cloud_Backend` Lambda integration to each route.
5. In **CORS Configuration**, configure:
   - **Access-Control-Allow-Origin:** `*`
   - **Access-Control-Allow-Headers:** `Content-Type,Authorization,X-Requested-With`
   - **Access-Control-Allow-Methods:** `GET,POST,PUT,DELETE,OPTIONS`

### Step 5: (Optional) Setup DynamoDB Streams & SNS Alerts
1. Create a topic in **Amazon SNS** named `fc-cloud-medical-alerts`.
2. Add an email subscription with your manager email address.
3. In DynamoDB table `players` > **Exports and streams**, click **Create trigger** and select `FC_Cloud_Backend` or deploy [`stream_processor.py`](stream_processor.py).
4. Whenever a player with `Injury` or `Knock` is registered, an automated email alert will be published instantly!

### Step 6: Deploy Frontend to Amazon S3
1. Create a public read or CloudFront-backed S3 bucket (e.g., `fc-cloud-manager-web`).
2. Upload [`frontend.html`](frontend.html) as `index.html`.
3. Update the `API_BASE_URL` in the `<script>` section of the HTML to your deployed API Gateway endpoint:
   ```javascript
   const API_BASE_URL = "https://<your-api-id>.execute-api.ap-southeast-2.amazonaws.com";
   ```

---

## 💻 Local Testing & Emulation

You can run `lambda_function.py` directly on your local machine without AWS credentials to test endpoints:

```bash
python lambda_function.py
```

The script will launch a lightweight local HTTP server at `http://127.0.0.1:8000`. You can test endpoints via cURL or Postman:

```bash
# Health Check
curl http://127.0.0.1:8000/

# Test Manager Login
curl -X POST http://127.0.0.1:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username":"manager","password":"admin123"}'
```

---

## 🔒 Security Best Practices
- **Least Privilege Access:** IAM roles only grant permissions required for specific DynamoDB tables.
- **Input Sanitization:** Strong data validation on both frontend forms and backend Lambda handlers.
- **WAF Protection:** AWS WAF inspects incoming requests for rate-limiting, SQLi, and unauthorized probing.
- **CORS Control:** Preflight `OPTIONS` support prevents browser cross-origin blocking.

---

## 👤 Manager & Club Information

- **Manager:** S. Mohamed Ashiq
- **Role:** First Team Manager
- **Club:** FC Cloud Rovers
- **Formation:** 4-3-3 Attack
- **Target Win Rate:** 85.0%+

