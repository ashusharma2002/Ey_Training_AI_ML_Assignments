# ─────────────────────────────────────────────────────────────
# main.py  ·  Entry point
#
# python main.py           base demo (notebook Steps 6-8)
# python main.py --ext 1   rolling compaction
# python main.py --ext 2   TTL + forget_fact
# python main.py --ext 3   parallel tool calls
# python main.py --ext 4   PII guard
# python main.py --ext 5   token accounting
# python main.py --ext 6   real Redis
# python main.py --chat    interactive REPL
# ─────────────────────────────────────────────────────────────

import argparse
from agent import Agent


# ── helpers ───────────────────────────────────────────────────

def say(agent: Agent, msg: str, verbose: bool = True):
    print(f"USER : {msg}")
    print(f"AGENT: {agent.chat(msg, verbose=verbose)}")
    print()


# ── base demo (Steps 6, 7, 8 from the notebook) ───────────────

def base_demo():
    a = Agent("base")
    print("─── Step 6: order lookup ────────────────────────────")
    say(a, "What is the status of order A1002?")

    print("─── Step 7: memory across turns ─────────────────────")
    say(a, "Remember that my shipping preference is express.")
    say(a, "What did I say my shipping preference was?")
    print("Facts in Redis :", a.mem.all_facts())
    print("History turns  :", a.mem.history_len())
    print()

    print("─── Step 8: multi-turn chat ─────────────────────────")
    for msg in [
        "Hi, I am Asha.",
        "How much was order A1003?",
        "Remember my budget cap is 500 dollars.",
        "Given my budget cap, was that order within it?",
    ]:
        say(a, msg, verbose=False)


# ── Extension 1: rolling summary / compaction ────────────────
# When history reaches 20 turns, oldest half is summarised by
# Haiku and replaced with one message. Context stays bounded.

def ext1_compaction():
    print("─── Extension 1: Rolling Compaction ─────────────────")
    a = Agent("ext1")
    msgs = [
        "What is order A1001?", "And A1002?", "And A1003?",
        "Remember my name is Asha.", "Remember shipping is express.",
        "What was A1001 again?", "How much was A1003?",
        "Remember budget is 500.", "What shipping did I prefer?",
        "Tell me about A1002.", "Status of A1001?",
    ]
    for msg in msgs:
        say(a, msg, verbose=False)
    print(f"History turns after compaction: {a.mem.history_len()}")


# ── Extension 2: TTL + forget_fact ───────────────────────────
# set_fact(ttl_seconds=N) → auto-expires after N seconds.
# forget_fact(key)        → removes one fact immediately.

def ext2_ttl_forget():
    print("─── Extension 2: TTL + forget_fact ──────────────────")
    import time
    from memory import RedisMemory

    m = RedisMemory("ext2-ttl")
    m.set_fact("promo", "SAVE20", ttl_seconds=2)
    print(f"Stored 'promo'   : {m.get_fact('promo')}")
    time.sleep(2.1)
    print(f"After 2s TTL     : {m.get_fact('promo')}  ← None (expired)")
    print()

    a = Agent("ext2-agent")
    say(a, "Remember my colour preference is blue.")
    say(a, "Forget my colour preference.")
    print("Facts after forget:", a.mem.all_facts())


# ── Extension 3: parallel tool calls ─────────────────────────
# Claude emits two tool_use blocks in one response.
# The loop answers both in a single round trip.

def ext3_parallel():
    print("─── Extension 3: Parallel Tool Calls ────────────────")
    a = Agent("ext3")
    say(a, (
        "For order A1001, give me the order details AND look up "
        "the customer details using the customer_id from that order."
    ), verbose=True)


# ── Extension 4: PII guard ────────────────────────────────────
# remember_fact rejects card numbers, emails, and phones.
# Returns is_error=True so Claude explains the refusal.

def ext4_pii():
    print("─── Extension 4: PII Guard ──────────────────────────")
    a = Agent("ext4")
    for msg in [
        "Store my card: 4111 1111 1111 1111.",    # blocked
        "Remember my email: asha@example.com.",   # blocked
        "Remember my phone: 9876543210.",          # blocked
        "Remember my note: leave at door.",        # allowed
    ]:
        say(a, msg, verbose=False)


# ── Extension 5: token accounting ────────────────────────────
# resp.usage read every step; totals printed at end_turn.

def ext5_tokens():
    print("─── Extension 5: Token Accounting ───────────────────")
    a = Agent("ext5")
    for msg in [
        "What is order A1002?",
        "And A1003?",
        "Remember my budget is 400.",
    ]:
        say(a, msg, verbose=True)


# ── Extension 6: real Redis ───────────────────────────────────
# Set REDIS_URL in .env → make_redis() connects to real Redis.
# RedisMemory is unchanged between fake and real modes.

def ext6_redis():
    import os
    from memory import RedisMemory
    url = os.environ.get("REDIS_URL", "").strip()
    print("─── Extension 6: Real Redis ──────────────────────────")
    print(f"REDIS_URL  : {'set → real Redis' if url else 'blank → fakeredis'}")

    m = RedisMemory("ext6")
    m.set_fact("mode", "real" if url else "fake")
    print(f"set_fact   : ok")
    print(f"get_fact   : {m.get_fact('mode')}")
    print("RedisMemory class unchanged between both modes ✓")


# ── interactive REPL ──────────────────────────────────────────

def chat():
    a = Agent("chat")
    print("Interactive  |  quit · reset · facts\n")
    while True:
        try:
            user = input("YOU: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not user:        continue
        if user == "quit":  break
        if user == "reset": a.reset(); print("(cleared)\n"); continue
        if user == "facts": print(a.mem.all_facts(), "\n"); continue
        print(f"AGENT: {a.chat(user, verbose=True)}\n")


# ── entry point ───────────────────────────────────────────────

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--ext",  type=int, choices=range(1, 7))
    p.add_argument("--chat", action="store_true")
    args = p.parse_args()

    runners = {1: ext1_compaction, 2: ext2_ttl_forget, 3: ext3_parallel,
               4: ext4_pii,        5: ext5_tokens,      6: ext6_redis}

    if   args.chat:        chat()
    elif args.ext in runners: runners[args.ext]()
    else:                  base_demo()
