import unittest
import mock
import fnmatch

import json

import chore_redis

class MockRedis(object):

    def __init__(self, host, port):

        self.host = host
        self.port = port
        self.channel = None

        self.data = {}
        self.messages = []

    def publish(self, channel, message):

        self.channel = channel
        self.messages.append(message)

    def set(self, key, value):

        self.data[key] = value

    def get(self, key):

        if key in self.data:
            return self.data[key]

        return None

    def keys(self, pattern):

        for key in sorted(self.data.keys()):
            if fnmatch.fnmatch(key, pattern):
                yield key.encode('utf-8')

class TestChoreRedis(unittest.TestCase):

    maxDiff = None

    @mock.patch("redis.StrictRedis", MockRedis)
    def setUp(self):

        self.chore_redis = chore_redis.ChoreRedis("data.com", 667, "stuff")

    def test___init___(self):

        self.assertEqual(self.chore_redis.redis.host, "data.com")
        self.assertEqual(self.chore_redis.redis.port, 667)
        self.assertEqual(self.chore_redis.channel, "stuff")

    def test_set(self):

        chore = {
            "id": "bump",
            "node": "bump",
            "person": "kid",
            "text": "things",
            "language": "en"
        }

        self.chore_redis.set(chore)

        self.assertEqual(self.chore_redis.redis.data, {
            "/chore/bump": json.dumps(chore)
        })

    def test_get(self):

        chore = {
            "id": "bump",
            "node": "bump",
            "person": "kid",
            "text": "things",
            "language": "en"
        }

        self.chore_redis.redis.data["/chore/bump"] = json.dumps(chore)

        self.assertEqual(self.chore_redis.get("bump"), chore)

        self.assertIsNone(self.chore_redis.get("dump"))

    @mock.patch("chore_redis.time.time")
    def test_speak(self, mock_time):

        mock_time.return_value = 7

        chore = {
            "id": "bump",
            "node": "bump",
            "person": "kid",
            "text": "things",
            "language": "en"
        }

        self.chore_redis.speak(chore, "hi")

        self.assertEqual(self.chore_redis.redis.channel, "stuff")
        self.assertEqual(json.loads(self.chore_redis.redis.messages[0]), {
            "timestamp": 7,
            "node": "bump",
            "text": "kid, hi",
            "language": "en"
        })

    def test_list(self):

        self.chore_redis.set({
            "id": "dump",
            "node": "dump",
            "person": "kid",
            "text": "people",
            "language": "en"
        })

        self.chore_redis.set({
            "id": "bump",
            "node": "bump",
            "person": "kid",
            "text": "stuff",
            "language": "en"
        })

        self.chore_redis.redis.set("blurp", 0)
        self.chore_redis.redis.set("/chore/bump/jump/chore", 0)
        self.chore_redis.redis.set("/chore/stump/chore/2018-11-25T12:34:56", 0)

        self.assertEqual(self.chore_redis.list(), [
            {
                "id": "bump",
                "node": "bump",
                "person": "kid",
                "text": "stuff",
                "language": "en"
            },
            {
                "id": "dump",
                "node": "dump",
                "person": "kid",
                "text": "people",
                "language": "en"
            }
        ])

    @mock.patch("chore_redis.time.time")
    def test_check(self, mock_time):

        mock_time.return_value = 7

        chore = {
            "id": "bump",
            "node": "bump",
            "person": "kid",
            "text": "things",
            "language": "en",
            "tasks": [
                {
                    "id": 0,
                    "start": 0
                },
                {
                    "id": 1,
                    "text": "wait it",
                    "paused": True
                },
                {
                    "id": 2,
                    "text": "do it"
                }
            ]
        }

        self.chore_redis.check(chore)

        self.assertEqual(chore, {
            "id": "bump",
            "node": "bump",
            "person": "kid",
            "text": "things",
            "language": "en",
            "tasks": [
                {
                    "id": 0,
                    "start": 0
                },
                {
                    "id": 1,
                    "text": "wait it",
                    "paused": True
                },
                {
                    "id": 2,
                    "text": "do it"
                }
            ]
        })

        chore["tasks"][0]["end"] = 0

        self.chore_redis.check(chore)

        self.assertEqual(chore, {
            "id": "bump",
            "node": "bump",
            "person": "kid",
            "text": "things",
            "language": "en",
            "tasks": [
                {
                    "id": 0,
                    "start": 0,
                    "end": 0
                },
                {
                    "id": 1,
                    "text": "wait it",
                    "paused": True,
                    "start": 7,
                    "notified": 7
                },
                {
                    "id": 2,
                    "text": "do it"
                }
            ]
        })
        self.assertEqual(json.loads(self.chore_redis.redis.messages[0]), {
            "timestamp": 7,
            "node": "bump",
            "text": "kid, you do not have to wait it yet",
            "language": "en"
        })

        chore["tasks"][1]["end"] = 0

        self.chore_redis.check(chore)

        self.assertEqual(chore, {
            "id": "bump",
            "node": "bump",
            "person": "kid",
            "text": "things",
            "language": "en",
            "tasks": [
                {
                    "id": 0,
                    "start": 0,
                    "end": 0
                },
                {
                    "id": 1,
                    "text": "wait it",
                    "paused": True,
                    "start": 7,
                    "notified": 7,
                    "end": 0
                },
                {
                    "id": 2,
                    "text": "do it",
                    "start": 7,
                    "notified": 7
                }
            ]
        })
        self.assertEqual(json.loads(self.chore_redis.redis.messages[1]), {
            "timestamp": 7,
            "node": "bump",
            "text": "kid, please do it",
            "language": "en"
        })

        chore["tasks"][2]["end"] = 0

        self.chore_redis.check(chore)

        self.assertEqual(chore, {
            "id": "bump",
            "node": "bump",
            "person": "kid",
            "text": "things",
            "language": "en",
            "notified": 7,
            "end": 7,
            "tasks": [
                {
                    "id": 0,   
                    "start": 0,
                    "end": 0
                },
                {
                    "id": 1,
                    "text": "wait it",
                    "paused": True,
                    "start": 7,
                    "notified": 7,
                    "end": 0
                },
                {
                    "id": 2,   
                    "text": "do it",
                    "start": 7,
                    "notified": 7,
                    "end": 0
                }
            ]
        })

        self.assertEqual(json.loads(self.chore_redis.redis.messages[2]), {
            "timestamp": 7,
            "node": "bump",
            "text": "kid, thank you. You did things",
            "language": "en"
        })

    @mock.patch("chore_redis.time.time")
    def test_create(self, mock_time):

        mock_time.return_value = 7

        template = {
            "text": "get ready",
            "language": "en",
            "tasks": [
                {
                    "text": "wake up"
                },
                {
                    "text": "get dressed"
                }
            ]
        }

        self.assertEqual(self.chore_redis.create(template, "kid", "bump"), {
            "id": "bump",
            "person": "kid",
            "node": "bump",
            "text": "get ready",
            "language": "en",
            "start": 7,
            "notified": 7,
            "tasks": [
                {
                    "id": 0,   
                    "text": "wake up",
                    "start": 7,
                    "notified": 7
                },
                {
                    "id": 1,   
                    "text": "get dressed"
                }
            ]
        })

        self.assertEqual(self.chore_redis.get("bump"), {
            "id": "bump",
            "person": "kid",
            "node": "bump",
            "text": "get ready",
            "language": "en",
            "start": 7,
            "notified": 7,
            "tasks": [
                {
                    "id": 0,   
                    "text": "wake up",
                    "start": 7,
                    "notified": 7
                },
                {
                    "id": 1,   
                    "text": "get dressed"
                }
            ]
        })
        self.assertEqual(json.loads(self.chore_redis.redis.messages[0]), {
            "timestamp": 7,
            "node": "bump",
            "text": "kid, time to get ready",
            "language": "en"
        })
        self.assertEqual(json.loads(self.chore_redis.redis.messages[1]), {
            "timestamp": 7,
            "node": "bump",
            "text": "kid, please wake up",
            "language": "en"
        })

    @mock.patch("chore_redis.time.time")
    def test_remind(self, mock_time):

        mock_time.return_value = 2

        chore = {
            "id": "bump",
            "node": "bump",
            "person": "kid",
            "text": "people",
            "language": "en",
            "delay": 3,
            "notified": 0,
            "start": 0,
            "tasks": [
                {
                    "id": 0,   
                    "text": "what it",
                    "notified": 0,
                    "interval": 5
                },
                {
                    "id": 1,   
                    "text": "done it",
                    "start": 0,
                    "end": 0,
                    "notified": 0,
                    "interval": 5
                },
                {
                    "id": 2,   
                    "text": "do it",
                    "start": 0,
                    "paused": True,
                    "notified": 0,
                    "delay": 3,
                    "interval": 5
                },
                {
                    "id": 3,   
                    "text": "not yet",
                    "notified": 0,
                    "interval": 5
                }
            ]
        }

        self.assertFalse(self.chore_redis.remind(chore))

        mock_time.return_value = 7

        self.assertFalse(self.chore_redis.remind(chore))

        chore["tasks"][2]["paused"] = False

        self.assertTrue(self.chore_redis.remind(chore))

        self.assertEqual(self.chore_redis.get("bump"), {
            "id": "bump",
            "node": "bump",
            "person": "kid",
            "text": "people",
            "language": "en",
            "delay": 3,
            "notified": 0,
            "start": 0,
            "tasks": [
                {
                    "id": 0,   
                    "text": "what it",
                    "notified": 0,
                    "interval": 5
                },
                {
                    "id": 1,   
                    "text": "done it",
                    "start": 0,
                    "end": 0,
                    "notified": 0,
                    "interval": 5
                },
                {
                    "id": 2,   
                    "text": "do it",
                    "start": 0,
                    "delay": 3,
                    "paused": False,
                    "notified": 7,
                    "interval": 5
                },
                {
                    "id": 3,   
                    "text": "not yet",
                    "notified": 0,
                    "interval": 5
                }
            ]
        })
        self.assertEqual(len(self.chore_redis.redis.messages), 1)

        self.assertEqual(json.loads(self.chore_redis.redis.messages[0]), {
            "timestamp": 7,
            "node": "bump",
            "text": "kid, please do it",
            "language": "en"
        })

        self.assertFalse(self.chore_redis.remind(chore))
        self.assertEqual(len(self.chore_redis.redis.messages), 1)


    @mock.patch("chore_redis.time.time")
    def test_next(self, mock_time):

        mock_time.return_value = 7

        chore = {
            "id": "bump",
            "node": "bump",
            "person": "kid",
            "text": "stuff",
            "language": "en",
            "tasks": [
                {
                    "id": 0,   
                    "text": "done it",
                    "start": 0,
                    "end": 0
                },
                {
                    "id": 1,   
                    "text": "do it",
                    "start": 0
                },
                {
                    "id": 2,   
                    "text": "next it"
                }
            ]
        }

        self.assertTrue(self.chore_redis.next(chore))
        self.assertEqual(self.chore_redis.get("bump"), {
            "id": "bump",
            "node": "bump",
            "person": "kid",
            "text": "stuff",
            "language": "en",
            "tasks": [
                {
                    "id": 0,   
                    "text": "done it",
                    "start": 0,
                    "end": 0
                },
                {
                    "id": 1,   
                    "text": "do it",
                    "start": 0,
                    "notified": 7,
                    "end": 7
                },
                {
                    "id": 2,   
                    "text": "next it",
                    "start": 7,
                    "notified": 7
                }
            ]
        })
        self.assertEqual(len(self.chore_redis.redis.messages), 2)
        self.assertEqual(json.loads(self.chore_redis.redis.messages[0]), {
            "timestamp": 7,
            "node": "bump",
            "text": "kid, you did do it",
            "language": "en"
        })
        self.assertEqual(json.loads(self.chore_redis.redis.messages[1]), {
            "timestamp": 7,
            "node": "bump",
            "text": "kid, please next it",
            "language": "en"
        })

        self.assertTrue(self.chore_redis.next(chore))
        self.assertEqual(self.chore_redis.get("bump"), {
            "id": "bump",
            "node": "bump",
            "person": "kid",
            "text": "stuff",
            "language": "en",
            "notified": 7,
            "end": 7,
            "tasks": [
                {
                    "id": 0,   
                    "text": "done it",
                    "start": 0,
                    "end": 0
                },
                {
                    "id": 1,   
                    "text": "do it",
                    "start": 0,
                    "notified": 7,
                    "end": 7
                },
                {
                    "id": 2,   
                    "text": "next it",
                    "start": 7,
                    "notified": 7,
                    "end": 7
                }
            ]
        })
        self.assertEqual(len(self.chore_redis.redis.messages), 4)
        self.assertEqual(json.loads(self.chore_redis.redis.messages[2]), {
            "timestamp": 7,
            "node": "bump",
            "text": "kid, you did next it",
            "language": "en"
        })
        self.assertEqual(json.loads(self.chore_redis.redis.messages[3]), {
            "timestamp": 7,
            "node": "bump",
            "text": "kid, thank you. You did stuff",
            "language": "en"
        })

        self.assertFalse(self.chore_redis.next(chore))
        self.assertEqual(self.chore_redis.get("bump"), {
            "id": "bump",
            "node": "bump",
            "person": "kid",
            "text": "stuff",
            "language": "en",
            "notified": 7,
            "end": 7,
            "tasks": [
                {
                    "id": 0,   
                    "text": "done it",
                    "start": 0,
                    "end": 0
                },
                {
                    "id": 1,   
                    "text": "do it",
                    "start": 0,
                    "notified": 7,
                    "end": 7
                },
                {
                    "id": 2,   
                    "text": "next it",
                    "start": 7,
                    "notified": 7,
                    "end": 7
                }
            ]
        })
        self.assertEqual(len(self.chore_redis.redis.messages), 4)

    @mock.patch("chore_redis.time.time")
    def test_pause(self, mock_time):

        mock_time.return_value = 7

        chore = {
            "id": "bump",
            "node": "bump",
            "person": "kid",
            "text": "stuff",
            "language": "en",
            "tasks": [
                {
                    "id": 0,   
                    "start": 0,
                    "text": "people"
                },
                {
                    "id": 1,   
                    "text": "stuff"
                },
                {
                    "id": 2,   
                    "text": "things"
                }
            ]
        }

        self.assertTrue(self.chore_redis.pause(chore, 0))
        self.assertEqual(self.chore_redis.get("bump"), {
            "id": "bump",
            "node": "bump",
            "person": "kid",
            "text": "stuff",
            "language": "en",
            "tasks": [
                {
                    "id": 0,
                    "start": 0,
                    "paused": True,
                    "notified": 7,
                    "text": "people"
                },
                {
                    "id": 1,   
                    "text": "stuff"
                },
                {
                    "id": 2,   
                    "text": "things"
                }
            ]
        })
        self.assertEqual(len(self.chore_redis.redis.messages), 1)
        self.assertEqual(json.loads(self.chore_redis.redis.messages[0]), {
            "timestamp": 7,
            "node": "bump",
            "text": "kid, you do not have to people yet",
            "language": "en"
        })

        self.assertFalse(self.chore_redis.pause(chore, 0))
        self.assertEqual(self.chore_redis.get("bump"), {
            "id": "bump",
            "node": "bump",
            "person": "kid",
            "text": "stuff",
            "language": "en",
            "tasks": [
                {
                    "id": 0,
                    "start": 0,
                    "paused": True,
                    "notified": 7,
                    "text": "people"
                },
                {
                    "id": 1,   
                    "text": "stuff"
                },
                {
                    "id": 2,   
                    "text": "things"
                }
            ]
        })
        self.assertEqual(len(self.chore_redis.redis.messages), 1)

    @mock.patch("chore_redis.time.time")
    def test_unpause(self, mock_time):

        mock_time.return_value = 7

        chore = {
            "id": "bump",
            "node": "bump",
            "person": "kid",
            "text": "stuff",
            "language": "en",
            "tasks": [
                {
                    "id": 0,   
                    "start": 0,
                    "paused": True,
                    "text": "people"
                },
                {
                    "id": 1,   
                    "text": "stuff"
                },
                {
                    "id": 2,   
                    "text": "things"
                }
            ]
        }

        self.assertTrue(self.chore_redis.unpause(chore, 0))
        self.assertEqual(self.chore_redis.get("bump"), {
            "id": "bump",
            "node": "bump",
            "person": "kid",
            "text": "stuff",
            "language": "en",
            "tasks": [
                {
                    "id": 0,
                    "start": 0,
                    "paused": False,
                    "notified": 7,
                    "text": "people"
                },
                {
                    "id": 1,   
                    "text": "stuff"
                },
                {
                    "id": 2,   
                    "text": "things"
                }
            ]
        })
        self.assertEqual(len(self.chore_redis.redis.messages), 1)
        self.assertEqual(json.loads(self.chore_redis.redis.messages[0]), {
            "timestamp": 7,
            "node": "bump",
            "text": "kid, you do have to people now",
            "language": "en"
        })

        self.assertFalse(self.chore_redis.unpause(chore, 0))
        self.assertEqual(self.chore_redis.get("bump"), {
            "id": "bump",
            "node": "bump",
            "person": "kid",
            "text": "stuff",
            "language": "en",
            "tasks": [
                {
                    "id": 0,
                    "start": 0,
                    "paused": False,
                    "notified": 7,
                    "text": "people"
                },
                {
                    "id": 1,   
                    "text": "stuff"
                },
                {
                    "id": 2,   
                    "text": "things"
                }
            ]
        })
        self.assertEqual(len(self.chore_redis.redis.messages), 1)

    @mock.patch("chore_redis.time.time")
    def test_skip(self, mock_time):

        mock_time.return_value = 7

        chore = {
            "id": "bump",
            "node": "bump",
            "person": "kid",
            "text": "stuff",
            "language": "en",
            "tasks": [
                {
                    "id": 0,   
                    "text": "people"
                },
                {
                    "id": 1,   
                    "text": "stuff"
                },
                {
                    "id": 2,   
                    "text": "things"
                }
            ]
        }

        self.assertTrue(self.chore_redis.skip(chore, 0))
        self.assertEqual(self.chore_redis.get("bump"), {
            "id": "bump",
            "node": "bump",
            "person": "kid",
            "text": "stuff",
            "language": "en",
            "tasks": [
                {
                    "id": 0,
                    "start": 7,
                    "skipped": True,
                    "notified": 7,
                    "end": 7,
                    "text": "people"
                },
                {
                    "id": 1,
                    "start": 7,
                    "notified": 7,
                    "text": "stuff"
                },
                {
                    "id": 2,   
                    "text": "things"
                }
            ]
        })
        self.assertEqual(len(self.chore_redis.redis.messages), 2)
        self.assertEqual(json.loads(self.chore_redis.redis.messages[0]), {
            "timestamp": 7,
            "node": "bump",
            "text": "kid, you do not have to people",
            "language": "en"
        })
        self.assertEqual(json.loads(self.chore_redis.redis.messages[1]), {
            "timestamp": 7,
            "node": "bump",
            "text": "kid, please stuff",
            "language": "en"
        })

        self.assertFalse(self.chore_redis.skip(chore, 0))
        self.assertEqual(len(self.chore_redis.redis.messages), 2)

    @mock.patch("chore_redis.time.time")
    def test_unskip(self, mock_time):

        mock_time.return_value = 7

        chore = {
            "id": "bump",
            "node": "bump",
            "person": "kid",
            "text": "stuff",
            "language": "en",
            "end": 0,
            "tasks": [
                {
                    "id": 0,
                    "start": 7,
                    "skipped": True,
                    "notified": 7,
                    "end": 7,
                    "text": "people"
                }
            ]
        }

        self.assertTrue(self.chore_redis.unskip(chore, 0))
        self.assertEqual(self.chore_redis.get("bump"), {
            "id": "bump",
            "node": "bump",
            "person": "kid",
            "text": "stuff",
            "language": "en",
            "notified": 7,
            "tasks": [
                {
                    "id": 0,
                    "start": 7,
                    "skipped": False,
                    "notified": 7,
                    "text": "people"
                }
            ]
        })
        self.assertEqual(len(self.chore_redis.redis.messages), 2)
        self.assertEqual(json.loads(self.chore_redis.redis.messages[0]), {
            "timestamp": 7,
            "node": "bump",
            "text": "kid, you do have to people",
            "language": "en"
        })
        self.assertEqual(json.loads(self.chore_redis.redis.messages[1]), {
            "timestamp": 7,
            "node": "bump",
            "text": "kid, I'm sorry but you did not stuff yet",
            "language": "en"
        })

        self.assertFalse(self.chore_redis.unskip(chore, 0))
        self.assertEqual(len(self.chore_redis.redis.messages), 2)

    @mock.patch("chore_redis.time.time")
    def test_complete(self, mock_time):

        mock_time.return_value = 7

        chore = {
            "id": "bump",
            "node": "bump",
            "person": "kid",
            "text": "stuff",
            "language": "en",
            "tasks": [
                {
                    "id": 0,   
                    "start": 0,
                    "text": "people"
                },
                {
                    "id": 1,   
                    "text": "stuff"
                },
                {
                    "id": 2,   
                    "text": "things"
                }
            ]
        }

        self.assertTrue(self.chore_redis.complete(chore, 0))
        self.assertEqual(self.chore_redis.get("bump"), {
            "id": "bump",
            "node": "bump",
            "person": "kid",
            "text": "stuff",
            "language": "en",
            "tasks": [
                {
                    "id": 0,   
                    "start": 0,
                    "notified": 7,
                    "end": 7,
                    "text": "people"
                },
                {
                    "id": 1,   
                    "start": 7,
                    "notified": 7,
                    "text": "stuff"
                },
                {
                    "id": 2,   
                    "text": "things"
                }
            ]
        })
        self.assertEqual(len(self.chore_redis.redis.messages), 2)
        self.assertEqual(json.loads(self.chore_redis.redis.messages[0]), {
            "timestamp": 7,
            "node": "bump",
            "text": "kid, you did people",
            "language": "en"
        })
        self.assertEqual(json.loads(self.chore_redis.redis.messages[1]), {
            "timestamp": 7,
            "node": "bump",
            "text": "kid, please stuff",
            "language": "en"
        })

        self.assertTrue(self.chore_redis.complete(chore, 2))
        self.assertEqual(self.chore_redis.get("bump"), {
            "id": "bump",
            "node": "bump",
            "person": "kid",
            "text": "stuff",
            "language": "en",
            "tasks": [
                {
                    "id": 0,   
                    "start": 0,
                    "notified": 7,
                    "end": 7,
                    "text": "people"
                },
                {
                    "id": 1,   
                    "start": 7,
                    "notified": 7,
                    "text": "stuff"
                },
                {
                    "id": 2,   
                    "start": 7,
                    "notified": 7,
                    "end": 7,
                    "text": "things"
                }
            ]
        })
        self.assertEqual(len(self.chore_redis.redis.messages), 3)
        self.assertEqual(json.loads(self.chore_redis.redis.messages[2]), {
            "timestamp": 7,
            "node": "bump",
            "text": "kid, you did things",
            "language": "en"
        })

        self.assertFalse(self.chore_redis.complete(chore, 2))
        self.assertEqual(self.chore_redis.get("bump"), {
            "id": "bump",
            "node": "bump",
            "person": "kid",
            "text": "stuff",
            "language": "en",
            "tasks": [
                {
                    "id": 0,   
                    "start": 0,
                    "notified": 7,
                    "end": 7,
                    "text": "people"
                },
                {
                    "id": 1,   
                    "start": 7,
                    "notified": 7,
                    "text": "stuff"
                },
                {
                    "id": 2,   
                    "start": 7,
                    "notified": 7,
                    "end": 7,
                    "text": "things"
                }
            ]
        })
        self.assertEqual(len(self.chore_redis.redis.messages), 3)

    @mock.patch("chore_redis.time.time")
    def test_incomplete(self, mock_time):

        mock_time.return_value = 7

        chore =  {
            "id": "bump",
            "node": "bump",
            "person": "kid",
            "text": "stuff",
            "language": "en",
            "end": 7,
            "tasks": [
                {
                    "id": 0,   
                    "start": 0,
                    "notified": 7,
                    "end": 7,
                    "text": "people"
                },
                {
                    "id": 1,   
                    "start": 7,
                    "notified": 7,
                    "text": "stuff"
                },
                {
                    "id": 2,   
                    "start": 7,
                    "notified": 7,
                    "end": 7,
                    "text": "things"
                }
            ]
        }

        self.assertTrue(self.chore_redis.incomplete(chore, 2))
        self.assertEqual(self.chore_redis.get("bump"), {
            "id": "bump",
            "node": "bump",
            "person": "kid",
            "text": "stuff",
            "language": "en",
            "notified": 7,
            "tasks": [
                {
                    "id": 0,   
                    "start": 0,
                    "notified": 7,
                    "end": 7,
                    "text": "people"
                },
                {
                    "id": 1,   
                    "start": 7,
                    "notified": 7,
                    "text": "stuff"
                },
                {
                    "id": 2,   
                    "start": 7,
                    "notified": 7,
                    "text": "things"
                }
            ]
        })
        self.assertEqual(len(self.chore_redis.redis.messages), 2)
        self.assertEqual(json.loads(self.chore_redis.redis.messages[0]), {
            "timestamp": 7,
            "node": "bump",
            "text": "kid, I'm sorry but you did not things yet",
            "language": "en"
        })
        self.assertEqual(json.loads(self.chore_redis.redis.messages[1]), {
            "timestamp": 7,
            "node": "bump",
            "text": "kid, I'm sorry but you did not stuff yet",
            "language": "en"
        })

        self.assertFalse(self.chore_redis.incomplete(chore, 2))
        self.assertEqual(self.chore_redis.get("bump"), {
            "id": "bump",
            "node": "bump",
            "person": "kid",
            "text": "stuff",
            "language": "en",
            "notified": 7,
            "tasks": [
                {
                    "id": 0,   
                    "start": 0,
                    "notified": 7,
                    "end": 7,
                    "text": "people"
                },
                {
                    "id": 1,   
                    "start": 7,
                    "notified": 7,
                    "text": "stuff"
                },
                {
                    "id": 2,   
                    "start": 7,
                    "notified": 7,
                    "text": "things"
                }
            ]
        })
        self.assertEqual(len(self.chore_redis.redis.messages), 2)
