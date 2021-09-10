# is-running [NonGen]
isRunning is an Automatic Uptime Detector, that checks endpoints and API-based Services and alerts a mailing list whenever the service is down. Helps in avoiding long duration service blockade.

The *NonGen or Non Generic* version of isRunning is aimed at personal usage as it doesn't have account creation privileges or multi-account support. The *Generic Version* will have Multi-account Support and support for Account Creation and other features that enable users to periodically check for Service Downtime.

Even though the Generic and NonGen version are a bit different, the API Endpoints and Access Flags will be similar. This Documentation will work as base for future versions of isRunning too.

## Architecture of isRunning

isRunning is a Python-Flask API Based Uptime Detector. The following is the architecture of isRunning.

![isRunning_Diagram](/documentation/isRunning-Architecture.jpg)


# Features 

- [x] On-demand Endpoint Check
- [x] EP Library to store Endpoints
- [x] Critical Alerts Mailing list 
- [x] Report Generation
- [x] Bulk Endpoint checks
- [ ] Routine Checks -  every 6 / 12 / 24 Hours (In Progress)
- [ ] Dashboard for isRunning
- [ ] Generic Version for Multi-user support

Check the Progress [here.](https://github.com/TanmoySG/is-running/projects/1)

# Documentation

The **EP Library** houses all the API-based Service Endpoints that are checked at regular Intervals for Uptime Detection.

isRunning functionalities can be Accessed using endpoints.

## Adding Endpoints to the EP Library

The EP Add Function can be accessed by calling the following EP by passing the payload.
```
Endpoint : /<mail>/add/endpoint
```
*mail* - Registered Email ID (username)

**Payload:**
```
{
    "password": <admin-password>,
    "endpoint":<ep-url> ,
    "name": <nickname-for-ep>,
    "description": <description-of-ep>,
    "recipients": [<recipient1-mail>, <recipient2-mail>],
    "routine" : <routine-check-schedule-in-hrs : 6/12/24>
}
```
- *endpoint* - URL of the Service Endpoint to be added to EP Library.

- *routine* - Scheduled Checks are run every few hours as specified using Routine. Currently for an EP, an auto-check runs every 6 or 12 or 24 Hours. Routine can be set as 6, 12 or 24.

- *recipients* - This defines the Emails that are to be notified when a downtime is detected.

- *password* - The Admin Password for the provided username/email

- *name* , *description* - Name and Description for the Given Endpoint.

## On-demand Uptime Check for EP in the EP Library

The on-demand EP Check Function can be accessed by calling the following EP.
```
Endpoint : /<mail>/check/endpoint
```
*mail* - Registered Email ID (username)

**Payload:**
```
{
    "password": <admin-password>,
    "endpoint": <ep-url>
}
```
- *endpoint* - URL of the Service Endpoint to be checked.

- *password* - The Admin Password for the provided username/email

When Downtime (HTTP Codes: 400 to 599) is detected for an EP, the members of the Mailing List of that EP are alerted through mail.

## On-demand Bulk Uptime Check for all EPs in the EP Library

All EPs in the EP Library can be checked for Uptime at once using this Endpoint.
```
Endpoint : /<mail>/check-all
```
*mail* - Registered Email ID (username)

**Payload:**
```
{
    "password": <admin-password>,
}
```

- *password* - The Admin Password for the provided username/email

When Downtime (HTTP Codes: 400 to 599) is detected for an EP, the members of the Mailing List of that EP are alerted through mail.

## Report Generation for all EPs in EP Library

Reports (in Text Format) can be generated and Mailed to the members of the Mailing List using this Endpoint.
```
Endpoint : /<mail>/generate/report/<type>
```
*mail* - Registered Email ID (username)

*type* - Type of Report to be generated.
 - cumulative - Cumulative Reports are a summary of Uptime of all EPs in the EP Library and are sent to the owner/admin only.

 - on-request - On-request reports are generated for particular EPs when requested. The "endpoint" payload item is required only for this type of report request.

 - each-owner - Standalone Reports are generated for each EP and sent to the Members of Mailing List. A cumulative summary report is also sent to the admin.

**Payload:**
```
{
    "password": <admin-password>,
    "endpoint": <url> // only for on-request
}
```

- *password* - The Admin Password for the provided username/email

- *endpoint* - EP to be checked on request. Only required for report type "on-request"

## EP Uptime check for non-EP Library Endpoints

Endpoints can be checked by external consumers to check their Endpoints without adding them to EP Library on-demand basis. These EPs are checked but not added to the EP Library and hence do not support Scheduled Checks. 
```
Endpoint : /check-uptime?endpoint=<endpoint>
```
- *endpoint* - Endpoint to be checked.

# Hosting

A Hosted Generic version of isRunning, when in Production Stage, will be implemented soon. 

Meanwhile, you can clone this project onto your server and fiddle with its functionalities.

*A Project by [TanmoySG](https://github.com/TanmoySG)*