# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v1.3.1] - 2023-03-29

### Features
- Added 'env' to Pipeline model - tasks can consume env as inputs
- Added 'params' to Pipeline model - tasks can consume params as inputs
- Added 'flavor' to the 'execution_profile' of the Task model
- Implemented execution_profile in task definition
- Updated OpenAPI spec to include model changes

### Breaking Changes
- N/A

### non-Breaking Changes
- Renamed 'container_run' type task to 'application'; Application aliased to container run to allow for backwards compatibility

### Fixed
- N/A

### Removed
- N/A

## [v1.3.0] - 2023-xx-xx

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

