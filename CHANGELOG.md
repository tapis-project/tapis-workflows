# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v1.3.0] - 2023-03-xx

### Features
- Engine streams service for streaming workflow execution logs via wss
- Tapis Job Task - enables users to submit jobs to the Tapis Jobs API in a workflow task
- Tapis Funtion Task - enables users to run arbitry code in select runtimes (currently only python39) 

### Breaking Changes
- Deployer - `pipelines` service renamed to `engine`

### non-Breaking Changes
- Added properties to the Pipeline model to enable tapis_job, function, and tapis_actor type tasks.

### Fixed
- N/A

### Removed
- N/A

