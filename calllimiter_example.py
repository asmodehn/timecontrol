#TODO : include in docs


# Because we need one limiter for multiple decorators
import asyncio
import time

from datetime import datetime

from timecontrol.calllimiter import calllimiter

limiter = calllimiter(ratelimit=3, timer=time.time)

# Here we show the one limiter / multiple command setup


@limiter
async def cmd1(*args):
    print(f"cmd1 ! {args}")
    return await asyncio.sleep(1)


@limiter
async def cmd2(*args):
    print(f"cmd2 ! {args}")
    return await asyncio.sleep(1)


if __name__ == '__main__':

    async def schedule():
        fc1 = cmd1("First command 1")
        sc1 = cmd1("Second command 1")
        fc2 = cmd2("Second command 2")
        sc2 = cmd2("First command 2")

        print(f"{datetime.now()}")
        await fc1  # will wait on init

        print(f"{datetime.now()}")
        time.sleep(3)  # preemptively waiting...

        print(f"{datetime.now()}")
        await fc2  # will NOT wait

        print(f"{datetime.now()}")
        await sc1  # will wait

        print(f"{datetime.now()}")
        time.sleep(3)  # preemptively waiting...

        print(f"{datetime.now()}")
        await sc2  # will NOT wait (common time limiter already satisfied)

    asyncio.run(schedule())

