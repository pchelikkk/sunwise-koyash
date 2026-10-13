# VM Deployment

Project: KOYASH  
Team: Sunwise  
Assignment: 4  
Release: v0.2.0

## Deployment purpose

The latest KOYASH MVP increment is deployed to the university VM so that the customer and teaching assistants can access and review the product remotely.

## Deployed MVP

`http://10.93.26.208:8080/`

## Deployed increment

The deployed version includes:

- latest adaptive MVP v1 prototype;
- static prototype assets;
- customer-facing questionnaire flow;
- recommendation result screen;
- product reasoning and feedback interaction;
- Sprint 2 / Assignment 4 release documentation.

## Deployment environment

- Platform: University VM
- Responsible person: team lead / backend developer
- Access type: HTTP access through university network
- Deployment URL: `http://10.93.26.208:8080/`

## Backend health endpoint

If backend is exposed separately, the health endpoint should be checked at:

`http://10.93.26.208:8000/health`

If the current VM deployment exposes only the static MVP prototype, the health endpoint is not publicly exposed in the deployed environment.

## Deployment verification

The deployment is considered successful if:

- the KOYASH MVP page opens from the VM URL;
- the latest adaptive prototype is visible;
- the questionnaire flow can be completed;
- the recommendation result screen is reachable;
- the product feedback interaction is available;
- the deployment link is included in the Week 4 report and release notes.

## Evidence

Deployment evidence can be added to:

`reports/week4/images/`

Recommended screenshots:

- deployed KOYASH page opened by VM URL;
- questionnaire screen;
- result screen;
- final GitLab release page;
- final passed GitLab pipeline, if available.