---
name: webiny
description: "Scaffold, extend, and deploy serverless Webiny CMS on AWS."
version: 0.1.0
author: Terrance (tee), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Webiny, Serverless, AWS, CMS, Headless, GraphQL, Nextjs]
    related_skills: [sdlc-review, plan]
---

# Webiny Serverless CMS Development & Deployment

Scaffold, develop, extend, and deploy Webiny Serverless Headless CMS, Page Builder, and custom GraphQL applications on AWS.

---

## 1. Quick Reference

| Action | Command |
|---|---|
| **Create Project** | `npx create-webiny-project my-webiny-project` |
| **Deploy Core / All** | `yarn webiny deploy` |
| **Deploy Specific App** | `yarn webiny deploy api --env dev` |
| **Watch / Local Dev** | `yarn webiny watch api/code/graphql --env dev` |
| **Destroy Infrastructure** | `yarn webiny destroy --env dev` |
| **Output Endpoints** | `yarn webiny output api --env dev` |

---

## 2. Project Initialization

To scaffold a new Webiny project (requires Node.js 18+ and configured AWS credentials):

```bash
# 1. Initialize project
npx create-webiny-project my-webiny-project

# 2. Enter project folder
cd my-webiny-project

# 3. Deploy to AWS environment
yarn webiny deploy --env dev
```

---

## 3. Architecture & Monorepo Structure

- **`api/`**: Serverless GraphQL API handlers (AWS Lambda & API Gateway), Page Builder, Form Builder, and Headless CMS plugins.
- **`apps/admin/`**: React-based Admin Area SPA (hosted on Amazon S3 + CloudFront).
- **`apps/website/`**: Public React website / Page Builder rendering engine.
- **`apps/theme/`**: Theme definitions, layouts, and style tokens.

---

## 4. Connecting Next.js Frontend (`website-builder-nextjs`)

To consume Webiny Headless CMS / Page Builder data from Next.js:

```bash
# Configure environment variables in Next.js
WEBINY_API_URL="https://your-api-id.cloudfront.net/cms/read/en-US"
WEBINY_API_TOKEN="your-api-token"
```

Query the Headless CMS via GraphQL:
```graphql
query ListArticles {
  listArticles {
    data {
      id
      title
      slug
      content
      featuredImage
    }
  }
}
```
