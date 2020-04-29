# FFF Transparency WG
## How to develop for the bot
To develop for the bot, a couple of steps need to be undertaken aside from forking and cloning the repository to your local PC.
The repository contains three branches:
- Master -> This branch is directly connected to the server on which is running the stable version of the code.
- Testing -> This branch is connected to a different server, which runs the code in development. This branch is used for testing before the code get's pushed to the master.
- Development -> This is the development branch of the repository. It is not tied to any server. This branch get's committed to the Testing branch.

To develop for this bot, add pull requests to the Development Branch.

After you fork and clone the development repository, you need to follow the steps below to be able to run the code on your local machine:
