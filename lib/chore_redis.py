"""
Main module for interacting with chores in Redis
"""

import time
import copy
import json

import redis


class ChoreRedis(object):
    """
    Main class for interacting with chores in Redis
    """

    def __init__(self, host, port, channel):

        self.redis = redis.StrictRedis(host=host, port=port)
        self.channel = channel

    def set(self, chore):
        """
        Sets a chore in Redis
        """

        # Just set using the node and dumped data

        self.redis.set(f"/chore/{chore['id']}", json.dumps(chore))

    def get(self, id):
        """
        Get chore from Redis
        """

        # Get the data and if it's there, parse and return.

        chore = self.redis.get(f"/chore/{id}")

        if chore:
            return json.loads(chore)

        # Else return none

        return None

    def speak(self, chore, text):
        """
        Says something on the speaking channel
        """

        # Follows the standards format

        self.redis.publish(self.channel, json.dumps({
            "timestamp": time.time(),
            "node": chore["node"],
            "text": f"{chore['person']}, {text}",
            "language": chore["language"]
        }))

    def list(self):
        """
        Lists nodes with an active chore
        """

        chores = []

        # Get all the keys in Redis matching our storage pattern

        for key in self.redis.keys('/chore/*'):
            pieces = key.decode("utf-8").split('/')

            # If we're sure there's nothing hinky, get the actual chore

            if len(pieces) == 3 and pieces[1] == "chore":
                chores.append(self.get(pieces[2]))

        return chores

    def check(self, chore):
        """
        Checks to see if there's tasks remaining, if so, starts one.
        If not completes the task
        """

        # Go through all the tasks

        for task in chore["tasks"]:

            # If there's one that's started and not completed, we're good

            if "started" in task and "completed" not in task:
                return

        # Go through the tasks again now that we know none are in progress

        for task in chore["tasks"]:

            # If not started, start it, and let 'em know

            if "started" not in task:
                task["started"] = time.time()
                task["notified"] = task["started"]
                self.speak(chore, f"please {task['text']}")
                return

        # If we're here, all are done, so complete the chore

        chore["completed"] = time.time()
        chore["notified"] = chore["completed"] 
        self.speak(chore, f"thank you. You did {chore['text']}")

    def create(self, template, person, node):
        """
        Creates a chore from a template
        """

        # Copy the template and add the person and node.

        chore = copy.deepcopy(template)
        chore.update({
            "id": node,
            "person": person,
            "node": node
        })
        for index, task in enumerate(chore["tasks"]):
            if "id" not in task:
                task["id"] = index

        # We've started the overall chore.  Notify the person
        # record that we did so.

        chore["started"] = time.time()
        chore["notified"] = chore["started"] 
        self.speak(chore, f"time to {chore['text']}")

        # Check for the first tasks and set our changes. 

        self.check(chore)
        self.set(chore)

        return chore

    def remind(self, chore):
        """
        Sees if any reminders need to go out
        """

        # Go through all the tasks

        for task in chore["tasks"]:

            # If this is the first active task

            if "started" in task and "completed" not in task:
                
                # If it has an interval and it's more been more than that since the last notification

                if "interval" in task and time.time() > task["notified"] + task["interval"]:

                    # Notify and sotre that we did, breaking out of the current chore 
                    # because we only want to notify one at a time

                    task["notified"] = time.time()
                    self.speak(chore, f"please {task['text']}")
                    self.set(chore)

                    return True

                # We've found the active task, so regardless we're done

                break

        return False

    def next(self, chore):
        """
        Completes the current task and starts the next. This is used
        with a button press.  
        """

        # Go through all the tasks, complete the first one found
        # that's ongoing and break

        for task in chore["tasks"]:
            if "started" in task and "completed" not in task:
                task["completed"] = time.time()
                task["notified"] = task["completed"]
                self.speak(chore, f"you did {task['text']}")

                # Check to see if there's another one and set

                self.check(chore)
                self.set(chore)

                return True

        return False

    def complete(self, chore, id):
        """
        Completes a specific task
        """

        task = chore["tasks"][id]

        # Complete if it isn't. 

        if "completed" not in task:

            task["completed"] = time.time()

            # If it hasn't been started, do so now

            if "started" not in task:
                task["started"] = task["completed"]

            task["notified"] = task["completed"]
            self.speak(chore, f"you did {task['text']}")

            # See if there's a next one, save our changes

            self.check(chore)
            self.set(chore)

            return True

        return False

    def incomplete(self, chore, id):
        """
        Undoes a specific task
        """

        task = chore["tasks"][id]

        # Delete completed from the task.  This'll leave the current task started.
        # It's either that or restart it.  This action is done if a kid said they
        # were done when they weren't.  So an extra penality is fine. 

        if "completed" in task:
            del task["completed"]
            task["notified"] = time.time()
            self.speak(chore, f"I'm sorry but you did not {task['text']} yet")

            # And incomplete the overall chore too if needed

            if "completed" in chore:
                del chore["completed"]
                self.speak(chore, f"I'm sorry but you did not {chore['text']} yet")

            # Don't check because we know one is started. But set out changes.

            self.set(chore)

            return True

        return False
