---
html: ledgers.html
parent: payment-system-basics.html
blurb: The XRP Ledger is composed of a series of individual ledgers, or ledger versions, which rippled keeps in its internal database. Learn about the structure and contents of these ledgers.
labels:
  - Blockchain
  - Data Retention
---
# Ledgers

The XRP Ledger is a shared, global ledger that is open to all. Individual participants can trust the integrity of the ledger without having to trust any single institution to manage it. The `rippled` server software accomplishes this by managing a ledger database that can only be updated according to very specific rules. Each instance of `rippled` keeps a full copy of the ledger, and the peer-to-peer network of `rippled` servers distributes candidate transactions among themselves. The consensus process determines which transactions get applied to each new version of the ledger. See also: [The Consensus Process](consensus.html).

{{ include_svg("img/ledger-changes.svg", "Diagram: Each ledger is the result of applying transactions to the previous ledger version.") }}

The shared global ledger is actually a series of individual ledgers, or ledger versions, which `rippled` keeps in its internal database. Every ledger version has a [Ledger Index][] which identifies the order in which ledgers occur. Each closed ledger version also has an identifying hash value, which uniquely identifies the contents of that ledger. At any given time, a `rippled` instance has an in-progress "current" open ledger, plus some number of closed ledgers that have not yet been approved by consensus, and any number of historical ledgers that have been validated by consensus. Only the validated ledgers are certain to be correct and immutable.

A single ledger version consists of several parts:

{{ include_svg("img/anatomy-of-a-ledger-simplified.svg", "Diagram: A ledger has transactions, a state tree, and a header with the close time and validation info") }}

* A **header** - The [Ledger Index][], hashes of its other contents, and other metadata.
* A **transaction tree** - The [transactions](transaction-formats.html) that were applied to the previous ledger to make this one. Transactions are the _only_ way to change the ledger.
* A **state tree** - All the [ledger objects](ledger-object-types.html) that contain the settings, balances, and objects in the ledger as of this version.


## Tree Format

As its name might suggest, a ledger's state tree is a tree data structure. Each object in the state tree is identified by a 256-bit object ID. In JSON, a ledger object's ID is the `index` field, which contains a 64-character hexadecimal string like `"193C591BF62482468422313F9D3274B5927CA80B4DD3707E42015DD609E39C94"`. Every object in the state tree has an ID that you can use to look up that object; every transaction has an identifying hash that you can use to look up the transaction in the transaction tree. Do not confuse the `index` (ID) of a ledger object with the [`ledger_index` (sequence number) of a ledger][Ledger Index].

**Tip:** Sometimes, an object in the ledger's state tree is called a "ledger node". For example, transaction metadata returns a list of `AffectedNodes`. Do not confuse this with a "node" (server) in the peer-to-peer network.

In the case of transactions, the identifying hash is based on the signed transaction instructions, but the contents of the transaction object when you look it up also contain the results and metadata of the transaction, which are not taken into account when generating the hash.

## Open, Closed, and Validated Ledgers

The `rippled` server makes a distinction between ledger versions that are _open_, _closed_, and _validated_. A server has one open ledger, any number of closed but unvalidated ledgers, and an immutable history of validated ledgers. The following table summarizes the difference:

| Ledger Type:                     | Open                        | Closed                                     | Validated |
|:---------------------------------|:----------------------------|:-------------------------------------------|:--|
| **Purpose:**                     | Temporary workspace         | Proposed next state                        | Confirmed previous state |
| **Number used:**                 | 1                           | Any number, but usually 0 or 1             | One per ledger index, growing over time |
| **Can contents change?**         | Yes                         | No, but the whole ledger could be replaced | Never |
| **Transactions are applied in:** | The order they are received | Canonical order                            | Canonical order |

Unintuitively, the XRP Ledger never "closes" an open ledger to convert it into a closed ledger. Instead, the server throws away the open ledger, creates a new closed ledger by applying transactions on top of a previous closed ledger, then creates a new open ledger using the latest closed ledger as a base. This is a consequence of [how consensus solves the double-spend problem](consensus-principles-and-rules.html#simplifying-the-problem).

For an open ledger, servers apply transactions in the order those transactions appear, but different servers may see transactions in different orders. Since there is no central timekeeper to decide which transaction was actually first, servers may disagree on the exact order of transactions that were sent around the same time. Thus, the process for calculating a closed ledger version that is eligible for [validation](consensus.html#validation) is different than the process of building an open ledger from proposed transactions in the order they arrive. To create a "closed" ledger, each XRP Ledger server starts with a set of transactions and a previous, or "parent", ledger version. The server puts the transactions in a canonical order, then applies them to the previous ledger in that order. The canonical order is designed to be deterministic and efficient, but hard to game, to increase the difficulty of front-running Offers in the [decentralized exchange](decentralized-exchange.html).

Thus, an open ledger is only ever used as a temporary workspace, which is a major reason why transactions' [tentative results may vary from their final results](finality-of-results.html).

## Ledger Close Times

The time that a ledger version closed is recorded at the `close_time` field of the [ledger header](ledger-header.html). To make it easier for the network to reach a consensus on an exact close time, this value is rounded to a number of seconds based on the close time resolution, currently 10 seconds. If rounding would cause a ledger's close time to be the same as (or earlier than) its parent ledger's, the child ledger has its close time set to the parent's close time plus 1. This guarantees that the close times of validated ledgers are strictly increasing. <!-- STYLE_OVERRIDE: a number of -->

Since new ledger versions usually close about every 3 to 5 seconds, these rules result in a loose pattern where ledgers' close times end in :00, :01, :02, :10, :11, :20, :21, and so on. Times ending in 2 are less common and times ending in 3 are very rare, but both occur randomly when more ledgers randomly happen to close within a 10-second window.

Generally speaking, the ledger cannot make any time-based measurements that are more precise than the close time resolution. For example, to check if an object has passed an expiration date, the rule is to compare it to the close time of the parent ledger. (The close time of a ledger is not yet known when executing transactions to go into that ledger.) This means that, for example, an [Escrow](escrow.html) could successfully finish at a real-world time that is up to about 10 seconds later than the time-based expiration specified in the Escrow object.

### Example

The following examples show the rounding behavior of ledger close times, from the perspective of an example validator, following a ledger with the close time **12:00:00**:

**Current consensus round**

1. A validator notes that it was **12:00:03** when the ledger closed and entered consensus. The validator includes this close time in its proposals.
2. The validator observes that most other validators (on its UNL) proposed a close time of 12:00:02, and one other proposed a close time of 12:00:03. It changes its proposed close time to match the consensus of **12:00:02**.
3. The validator rounds this value to the nearest close time interval, resulting in **12:00:00**.
4. Since 12:00:00 is not greater than the previous ledger's close time, the validator adjusts the close time to be exactly 1 second after the previous ledger's close time. The result is an adjusted close time of **12:00:01**.
5. The validator builds the ledger with these details, calculates the resulting hash, and confirms in the [validation step](consensus.html#validation) that others did the same.

Non-validating servers do all the same steps, except they don't propose their recorded close times to the rest of the network.

**Next consensus round**

1. The next ledger enters consensus at **12:00:04** according to most validators.
2. This rounds down again, to a close time of **12:00:00**.
3. Since this is not greater than the previous ledger's close time of 12:00:01, the adjusted close time is **12:00:02**.

**Next consensus round after that**

1. The ledger after that enters consensus at **12:00:05** according to most validators.
2. This rounds up, based on the close time resolution, to **12:00:10**.
3. Since this value is larger than the previous ledger's close time, it does not need to be adjusted. **12:00:10** becomes the official close time.

## See Also

- For more information about ledger headers, ledger object IDs, and ledger object types, see [Ledger Data Formats](ledger-data-formats.html)
- For information on how servers track the history of changes to ledger state, see [Ledger History](ledger-history.html)


<!--{# common link defs #}-->
{% include '_snippets/rippled-api-links.md' %}
{% include '_snippets/tx-type-links.md' %}
{% include '_snippets/rippled_versions.md' %}
