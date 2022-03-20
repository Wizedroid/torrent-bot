# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.0.3-alpha] - 2022-03-20

- Added RotatingFileHandler and StreamHandler to log both to a file and stdout
- Added new function to tv show probe to parse datetime with support for known imdb formats
- Added cache for imdb finder (fetch_show)

## [0.0.2-alpha] - 2022-03-19

- Changed the README file to include the new installation methods.
- Changed the README file to remove unused sections from the content table and updated some references
- Changed template folder for when running as executable (Fixes Executable for 0.0.1-alpha)

## [0.0.1-alpha] - 2022-03-18

- Creation of a bot that automatically searches movies and tv series using entries previously added to a database
- Frontend written using Flask's framework to allow users to add tv series and movies to the database
- Support for searching movies using imdb database supported by cinamagoer
- Support for searching tv series using imdb database supported by cinamagoer
- Support for adding imdb search results directly to the database which get automatically monitored for download
- Support for downloading full seasons or episodes of a tv show (currently no support for downloading a tv series as a whole)