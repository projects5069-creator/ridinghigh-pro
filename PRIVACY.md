# Privacy Policy

**Last updated: May 11, 2026**

## Overview

RidingHigh Pro ("the Application") is a personal automated trading research tool developed and operated solely by Amihay Levy for personal use. This Privacy Policy describes how the Application interacts with Google services.

## Information We Access

The Application accesses the following Google services on behalf of the authorized user:

- **Google Drive API** (`https://www.googleapis.com/auth/drive`): Used to create, read, and manage Google Sheets files within the user's own Google Drive. The Application does not access, read, or modify any files other than those it creates.

- **Google Sheets API** (`https://www.googleapis.com/auth/spreadsheets`): Used to read and write trading scan data, analysis results, and operational logs to Google Sheets owned by the user.

## How We Use Information

All data accessed via Google services is used exclusively for the following purposes:

1. Storing market scan results from public financial data sources (FINVIZ, Alpaca, Yahoo Finance)
2. Logging algorithmic trading decisions for analysis and audit purposes
3. Generating performance reports and dashboards for the authorized user
4. Maintaining operational logs (system health, errors, backups)

## Data Storage and Retention

- All data is stored in the authorized user's own Google Drive account.
- The Application does not transmit data to any third-party servers other than:
  - Google services (Drive, Sheets, OAuth)
  - Alpaca Markets API (paper trading data)
  - Public financial data providers (FINVIZ, Yahoo Finance, Finnhub) for read-only market data
- No data is shared with, sold to, or transmitted to any other party.

## Data Sharing

We do not share, sell, rent, or trade any user data with any third party. The Application operates entirely within the authorized user's own infrastructure and Google account.

## Security

- All authentication is performed via Google OAuth 2.0.
- Refresh tokens are stored as encrypted GitHub Actions secrets.
- API credentials are never logged or transmitted in plaintext.
- The Application runs in a private GitHub repository accessible only to the authorized user.

## User Rights

The authorized user can at any time:
- Revoke the Application's access via Google Account settings (https://myaccount.google.com/permissions)
- Delete all data stored in their Google Drive
- Discontinue use of the Application

## Children's Privacy

The Application is not intended for use by individuals under 18 years of age.

## Changes to This Policy

This Privacy Policy may be updated periodically. Changes will be reflected in the "Last updated" date at the top of this document.

## Contact

For questions regarding this Privacy Policy, contact:

**Email:** projects5069@gmail.com
**Repository:** https://github.com/projects5069-creator/-ridinghigh-pro

---

*RidingHigh Pro is a personal research tool. It is not a commercial service, does not have users beyond the developer, and does not collect, store, or process any third-party personal information.*
