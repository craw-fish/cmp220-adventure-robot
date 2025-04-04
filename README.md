# Adventure Robot
Collaborative final project for CMP220 (Spring 2025)
- [Uploading to the API](#uploading)
- [Retrieving from the API](#retrieving)

## Using the API

### Uploading

First, a **robot** must be registered in the database. This is done via a POST request to the Robots endpoint, specifying `robot_name`. The database will add an entry for this robot to the Robots table, with an auto-incrementing `robot_id` (the first will be assigned 1, subsequent entries count up).

<details>
<summary><b>Example: Registering a robot</b></summary>

```sh
curl -X POST "http://localhost:5001/robots" \
     -F "robot_name=Justin"
```
</details>

<br>

Note that robot data may also be overwritten by specifying an existing `robot_id`.

<details>
<summary><b>Example: Changing a robot's name</b></summary>

```sh
curl -X POST "http://localhost:5001/robots" \
     -F "robot_id=1"
     -F "robot_name=PhilBot"
```
</details>

<br>

Afterwards, **“snapshots”** from the robot’s journey can be uploaded to the Snapshots endpoint. Any such POST request may contain the following arguments: \
*(\* = required)*
- `*` `photo`: local path to the photo associated with the snapshot (jpg, jpeg, or png)
- `*` `timestamp`: time when the photo was taken (YYYY-MM-DD HH:MM:SS)
- `*` `robot_id`: numeric ID of associated robot (refer to Robots table)
- `instruction`: last instruction robot received prior to snapshot

<details>
<summary><b>Example: Uploading a snapshot</b></summary>

```sh
curl -X POST "http://localhost:5001/snapshots" \
     -F "photo=@/Users/max.crawford/Desktop/placeholder.png" \
     -F "timestamp=2025-04-01 12:01:23" \
     -F "instruction=move forward" \
     -F "robot_id=1"
```
</details>

### Retrieving
**Robot** data may be accessed via the Robots endpoint. Without any query arguments, all robots are returned as a list of JSON objects. Each object contains the `robot_id` [int] and `robot_name` [str].

<details>
<summary><b>Example: All robots</b></summary>

```sh
curl -X GET "http://localhost:5001/robots"
```
```json
[
  {
    "robot_id": 1,
    "robot_name": "Justin"
  },
  {
    "robot_id": 2,
    "robot_name": "Dustin"
  }
]
```
</details>

<br>

To retrieve information about particular robots, the following may be queried:
- `robot_id` to select a particular robot
- `robot_name` to search by the name field (supports wildcards)

<details>
<summary><b>Example: Robots by ID</b></summary>

```sh
curl -X GET "http://localhost:5001/robots/?robot_id=1"
```
```json
[
  {
    "robot_id": 1,
    "robot_name": "Justin"
  }
]
```
</details>
<details>
<summary><b>Example: Robots by name</b></summary>

```sh
curl -X GET "http://localhost:5001/robots?robot_name=%stin"
```
```json
[
  {
    "robot_id": 1,
    "robot_name": "Justin"
  },
  {
    "robot_id": 2,
    "robot_name": "Dustin"
  }
]
```
</details>

<br>

**Snapshot** data may be accessed via the Snapshots endpoint. Without any query arguments, all snapshots are displayed as a list of JSON objects. Each object contains the following fields:\
*(\* = non-nullable)*
- `*` `robot` [object]: contains `robot_id` [int] and `robot_name` [str] of associated robot
- `*` `photo_url` [str]: URL to the snapshot photo, accessible via API as a static image file
- `*` `snapshot_id` [int]: unique ID for the snapshot (auto-incrementing from 1)
- `*` `timestamp` [str]: time when the associated photo was taken
- `instruction` [str]: last instruction robot received prior to snapshot
- `description` [str]: a generated “caption” for the snapshot, describing the robot’s journey
  
<details>
<summary><b>Example: All snapshots</b></summary>

```sh
curl -X GET "http://localhost:5001/snapshots"
```
```json
[
  {
    "robot": {
      "robot_id": 1,
      "robot_name": "Justin"
    },
    "photo_url": "http://localhost:5001/snapshots/AdK5Kywr4eMCvA2immSYEQ.png",
    "snapshot_id": 1,
    "timestamp": "2025-04-01T12:01:23",
    "instruction": "move forward",
    "description": null
  },
  {
    "robot": {
      "robot_id": 1,
      "robot_name": "Justin"
    },
    "photo_url": "http://localhost:5001/snapshots/XpeqTcyLcCjuQHCSrWEhf2.png",
    "snapshot_id": 2,
    "timestamp": "2025-04-01T12:05:00",
    "instruction": null,
    "description": null
  },
  {
    "robot": {
      "robot_id": 2,
      "robot_name": "Dustin"
    },
    "photo_url": "http://localhost:5001/snapshots/JkE43eBbfRXcPs4rmtByrh.png",
    "snapshot_id": 3,
    "timestamp": "2025-04-02T00:00:01",
    "instruction": "move backward",
    "description": null
  }
]
```
</details>

<br>

Snapshots may be queried by the following fields:
- `robot_id` for snapshots associated with a particular robot
- `snapshot_id` for a particular snapshot
- `t_start` and/or `t_end` for a range of timestamps; specifying one while leaving the other blank searches “since” or “prior to” the given time (YYYY-MM-DD HH:MM:SS)
- `instruction` to search by the instruction field (supports wildcards)

<details>
<summary><b>Example: Snapshots filtered</b></summary>

```sh
curl -X GET "http://localhost:5001/snapshots?t_start=2025-04-01%2012:05:00&robot_id=2"
```
```json
[
  {
    "robot": {
      "robot_id": 2,
      "robot_name": "Dustin"
    },
    "photo_url": "http://localhost:5001/snapshots/JkE43eBbfRXcPs4rmtByrh.png",
    "snapshot_id": 3,
    "timestamp": "2025-04-02T00:00:01",
    "instruction": "move backward",
    "description": null
  }
]
```
</details>
