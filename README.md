PinBoard – A Pinterest-Style Image Sharing App (Flask + PostgreSQL)

PinBoard is a modern Pinterest-like web application that makes use of Flask, PostgreSQL, and a clean UI inspired by Pinterest.

Users can upload pins, view a live home feed, share pins in direct messages, chat with each other, and manage account settings.

This project includes:
User authentication: signup, login, logout
Pin uploads with image preview
* Real-time home feed (auto-refresh of new uploads)
Real-time messaging - DMs auto-update without refresh
* Share any pin directly into DM via a pop-up
* Live user search - for messages & sharing
* Clean frontend with Bootstrap

* Flask backend + SQLAlchemy + LoginManager

* Folder-based project structure and templates

Features

 Authentication

User sign up with username + email + password

Secure password hashing

Login / logout

Session-based auth using Flask-Login

Upload images (JPG, PNG, GIF)

Live preview while selecting image

Pins saved in /static/uploads/

Home feed will refresh automatically every 5 seconds.

Share pin button opens a floating popup with username search

Real-time messaging

Private one-to-one DM chatting

Send text messages

Share pins inside DM

Messages update every 3 seconds using polling
