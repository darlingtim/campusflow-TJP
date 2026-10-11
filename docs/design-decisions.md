# CampusFlow — Design Decisions

## 1. Project Overview

CampusFlow is a ticket management system designed to help users report, prioritize, view, and assign campus-related issues. It provides a structured way to manage issues such as network failures, hardware malfunctions, and software problems, making it easier to track reported issues and coordinate their resolution.

## 2. Ticket Status Decision

One of the key design discussions concerned the initial status of a ticket after submission. We considered whether a newly created ticket should be marked as `open` or `in progress`, since both indicate that the issue has not yet been resolved.

The distinction is important: `open` indicates that a ticket has been reported but work has not yet begun, while `in progress` indicates that someone is actively working on it. A ticket should only be considered resolved when the reported issue has been addressed.

This distinction provides a clearer understanding of a ticket's progress and helps prevent newly submitted issues from appearing to be actively worked on before anyone has started.

## 3. Feature Distribution and Task Management

The project was divided into six major features. As a team, we discussed how to distribute the workload and assigned responsibilities among members according to the features they would implement.

To support this process, we created GitHub issues for the individual features and assigned each issue to the relevant team member. This gave everyone a clear area of responsibility and helped us organize, track, and coordinate our progress throughout development.

Using GitHub issues provided a shared reference for the work to be done and made it easier to understand how each person's contribution fitted into the overall project.

## 4. Team Collaboration

Although each team member made valuable contributions, the success of CampusFlow depended on our collective effort, communication, and willingness to work towards a shared goal.

The process required us to discuss design choices, divide tasks, implement individual features, and bring our contributions together into a functioning application. This reinforced the importance of collaboration and clear responsibility in software engineering.

## 5. Acknowledgements

I would like to express my special appreciation to **Timothy Ododo and Joy Ayande** for their exceptional dedication to this project. They invested significant time, effort, and commitment in helping us move the work forward.

While every team member did their best, their contributions and willingness to give so much of their time made a meaningful difference to the project's success.

I am grateful to them and to the entire team for the collective effort that brought CampusFlow to completion. This achievement reflects the value of teamwork, commitment, and shared responsibility.

## 6. Conclusion

The development of CampusFlow involved more than implementing features. It required us to make decisions about how tickets should behave, organize responsibilities, track tasks, and collaborate towards a common objective.

These experiences helped us appreciate the importance of thoughtful design decisions, effective task management, and teamwork in delivering a successful software project.