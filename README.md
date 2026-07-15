# Mini Cryptocurrency Blockchain dengan Escrow Smart Contract

Project ini merupakan implementasi mini cryptocurrency blockchain dengan escrow smart contract. Sistem dibuat menggunakan Python dan Flask sebagai REST API. Sistem ini memiliki fitur wallet, digital signature, transaksi, mempool, mining, verifikasi blockchain, dan escrow smart contract.

Escrow smart contract digunakan untuk mengatur transaksi antara buyer dan seller dengan bantuan arbiter. Dana dari buyer akan dikunci terlebih dahulu di dalam escrow. Jika transaksi berjalan normal, dana akan dilepaskan kepada seller. Jika terjadi masalah, arbiter dapat menyelesaikan dispute dengan refund kepada buyer atau release kepada seller.

---

## Fitur Utama

- Membuat wallet baru
- Membuat dan memverifikasi transaksi dengan digital signature
- Menyimpan transaksi pending ke dalam mempool
- Melakukan mining untuk membuat block baru
- Memberikan coinbase reward kepada miner
- Deploy escrow smart contract
- Menjalankan normal escrow flow
- Menjalankan dispute dan refund flow
- Memverifikasi validitas blockchain
- Mendeteksi tampering pada data blockchain
- Melakukan pengujian negatif seperti replay nonce, invalid role, invalid transition, double release, dan altered payload

---

## Teknologi yang Digunakan

- Python
- Flask
- ECDSA
- JSON file storage
- Postman untuk pengujian API

---

## Struktur Folder

```text
project/
├── data/
│   ├── blockchain.json
│   ├── mempool.json
│   ├── balances.json
│   ├── contracts.json
│   └── wallets.json
│
├── models/
│   ├── block.py
│   ├── transaction.py
│   ├── wallet.py
│   └── contract.py
│
├── routes/
│   ├── blockchain.py
│   ├── transaction.py
│   ├── wallet.py
│   ├── contract.py
│   └── debug.py
│
├── services/
│   ├── blockchain.py
│   ├── wallet.py
│   ├── mempool.py
│   ├── mining.py
│   ├── validator.py
│   └── escrow.py
│
├── storage/
│   ├── chain.py
│   └── json_storage.py
│
└── main.py
```

---

## Instalasi

Install dependency yang dibutuhkan:

```bash
pip install flask ecdsa
```

Atau jika menggunakan `requirements.txt`:

```bash
pip install -r requirements.txt
```

Contoh isi `requirements.txt`:

```text
Flask
ecdsa
```

---

## Menjalankan Aplikasi

Jalankan Flask API dengan perintah:

```bash
python main.py
```

Server akan berjalan di:

```text
http://127.0.0.1:5000
```

---

## File Penyimpanan Data

Sistem menggunakan file JSON sebagai media penyimpanan data.

| File              | Fungsi                                           |
| ----------------- | ------------------------------------------------ |
| `blockchain.json` | Menyimpan daftar block yang sudah dibuat         |
| `mempool.json`    | Menyimpan transaksi yang menunggu proses mining  |
| `balances.json`   | Menyimpan saldo setiap wallet                    |
| `contracts.json`  | Menyimpan data escrow contract dan order         |
| `wallets.json`    | Menyimpan wallet lokal untuk kebutuhan pengujian |

---

## Endpoint API

| Endpoint                                | Method | Fungsi                            |
| --------------------------------------- | ------ | --------------------------------- |
| `/wallet/create`                        | POST   | Membuat wallet baru               |
| `/wallet/<address>/balance`             | GET    | Melihat saldo wallet              |
| `/tx/transfer`                          | POST   | Membuat transaksi transfer        |
| `/verify_tx`                            | POST   | Memverifikasi transaksi           |
| `/contract/deploy`                      | POST   | Membuat transaksi deploy contract |
| `/contract/call`                        | POST   | Memanggil method escrow contract  |
| `/contract/<address>`                   | GET    | Melihat data contract             |
| `/contract/<address>/orders/<order_id>` | GET    | Melihat data order                |
| `/mempool`                              | GET    | Melihat transaksi pending         |
| `/mine`                                 | POST   | Melakukan mining                  |
| `/chain`                                | GET    | Melihat isi blockchain            |
| `/verify_chain`                         | GET    | Memverifikasi blockchain          |
| `/balances`                             | GET    | Melihat seluruh balance           |
| `/debug/reset`                          | POST   | Me-reset data untuk pengujian     |

---

## Alur Kerja Sistem

Pada sistem ini, endpoint seperti `/contract/deploy` dan `/contract/call` tidak langsung mengubah state contract. Endpoint tersebut hanya membuat transaksi dan memasukkannya ke dalam mempool.

Perubahan state baru terjadi setelah proses mining dilakukan.

Alur umumnya:

```text
Request API
→ Transaksi dibuat dan ditandatangani
→ Transaksi masuk ke mempool
→ Mining dilakukan
→ Transaksi dimasukkan ke block
→ Balance atau contract state diperbarui
```

---

## Escrow Smart Contract Flow

### Normal Flow

```text
CREATED → FUNDED → SHIPPED → COMPLETED
```

Penjelasan:

1. Buyer membuat order menggunakan `create_order`
2. Buyer mengunci dana menggunakan `fund_order`
3. Seller mengonfirmasi pengiriman menggunakan `confirm_shipment`
4. Buyer mengonfirmasi barang diterima menggunakan `confirm_received`
5. Dana dilepaskan kepada seller

### Dispute / Refund Flow

```text
FUNDED / SHIPPED → DISPUTED → REFUNDED
```

Penjelasan:

1. Buyer membuat dan mendanai order
2. Buyer atau seller mengajukan dispute menggunakan `raise_dispute`
3. Arbiter menyelesaikan dispute menggunakan `resolve_dispute`
4. Jika keputusan adalah `REFUND_BUYER`, dana dikembalikan kepada buyer

---

## Contoh Pengujian Menggunakan Postman

### 1. Reset Data tanpa Menghapus Wallet

```http
POST /debug/reset
```

Body:

```json
{
  "clear_wallets": false
}
```

Endpoint ini akan menghapus data blockchain, mempool, balances, dan contracts, tetapi tetap menyimpan wallet yang sudah dibuat.

---

### 2. Membuat Wallet

```http
POST /wallet/create
```

Wallet yang dibuat dapat digunakan sebagai:

- Owner
- Buyer
- Seller
- Arbiter
- Miner

---

### 3. Memberikan Saldo Awal ke Buyer

Buyer membutuhkan saldo untuk melakukan `fund_order`.

```http
POST /mine
```

Body:

```json
{
  "miner_address": "<buyer_address>"
}
```

Setelah mining, buyer akan menerima coinbase reward.

---

### 4. Deploy Escrow Contract

```http
POST /contract/deploy
```

Body:

```json
{
  "owner": "<owner_address>",
  "nonce": 1
}
```

Setelah itu lakukan mining:

```http
POST /mine
```

Body:

```json
{
  "miner_address": "<miner_address>"
}
```

Contract baru akan aktif setelah transaksi deploy diproses melalui mining.

---

## Pengujian Normal Escrow Flow

### Create Order

```http
POST /contract/call
```

Body:

```json
{
  "contract_address": "<contract_address>",
  "method": "create_order",
  "params": {
    "order_id": "ORDER-001",
    "seller": "<seller_address>",
    "arbiter": "<arbiter_address>",
    "amount": 50,
    "item_description": "Mechanical Keyboard"
  },
  "caller": "<buyer_address>",
  "nonce": 1
}
```

Setelah itu lakukan mining.

### Fund Order

```http
POST /contract/call
```

Body:

```json
{
  "contract_address": "<contract_address>",
  "method": "fund_order",
  "params": {
    "order_id": "ORDER-001"
  },
  "caller": "<buyer_address>",
  "nonce": 2
}
```

Setelah itu lakukan mining.

### Confirm Shipment

```http
POST /contract/call
```

Body:

```json
{
  "contract_address": "<contract_address>",
  "method": "confirm_shipment",
  "params": {
    "order_id": "ORDER-001"
  },
  "caller": "<seller_address>",
  "nonce": 1
}
```

Setelah itu lakukan mining.

### Confirm Received

```http
POST /contract/call
```

Body:

```json
{
  "contract_address": "<contract_address>",
  "method": "confirm_received",
  "params": {
    "order_id": "ORDER-001"
  },
  "caller": "<buyer_address>",
  "nonce": 3
}
```

Setelah itu lakukan mining.

Cek hasil order:

```http
GET /contract/<contract_address>/orders/ORDER-001
```

Hasil akhir yang diharapkan:

```json
{
  "status": "COMPLETED",
  "locked_amount": 0
}
```

---

## Pengujian Dispute dan Refund

### Create Order

```http
POST /contract/call
```

Body:

```json
{
  "contract_address": "<contract_address>",
  "method": "create_order",
  "params": {
    "order_id": "ORDER-002",
    "seller": "<seller_address>",
    "arbiter": "<arbiter_address>",
    "amount": 50,
    "item_description": "Gaming Mouse"
  },
  "caller": "<buyer_address>",
  "nonce": 4
}
```

Setelah itu lakukan mining.

### Fund Order

```http
POST /contract/call
```

Body:

```json
{
  "contract_address": "<contract_address>",
  "method": "fund_order",
  "params": {
    "order_id": "ORDER-002"
  },
  "caller": "<buyer_address>",
  "nonce": 5
}
```

Setelah itu lakukan mining.

### Raise Dispute

```http
POST /contract/call
```

Body:

```json
{
  "contract_address": "<contract_address>",
  "method": "raise_dispute",
  "params": {
    "order_id": "ORDER-002",
    "reason": "Item was not received"
  },
  "caller": "<buyer_address>",
  "nonce": 6
}
```

Setelah itu lakukan mining.

### Resolve Dispute

```http
POST /contract/call
```

Body:

```json
{
  "contract_address": "<contract_address>",
  "method": "resolve_dispute",
  "params": {
    "order_id": "ORDER-002",
    "decision": "REFUND_BUYER",
    "reason": "Buyer claim accepted"
  },
  "caller": "<arbiter_address>",
  "nonce": 1
}
```

Setelah itu lakukan mining.

Cek hasil order:

```http
GET /contract/<contract_address>/orders/ORDER-002
```

Hasil akhir yang diharapkan:

```json
{
  "status": "REFUNDED",
  "locked_amount": 0
}
```

---

## Verify Chain

Untuk memastikan blockchain masih valid:

```http
GET /verify_chain
```

Hasil yang diharapkan:

```json
{
  "success": true,
  "message": "Chain is valid"
}
```

---

## Tampering Test

Tampering test dilakukan dengan mengubah salah satu data pada file `blockchain.json` secara manual. Setelah data diubah, jalankan kembali:

```http
GET /verify_chain
```

Hasil yang diharapkan:

```json
{
  "success": false,
  "message": "Invalid block hash at height ..."
}
```

Hal ini menunjukkan bahwa sistem dapat mendeteksi perubahan data pada blockchain.

---

## Pengujian Negatif

Beberapa pengujian negatif yang dilakukan:

- Replay nonce
- Invalid role
- Invalid transition
- Double release
- Altered payload

Contoh hasil yang diharapkan:

| Pengujian          | Hasil                                                     |
| ------------------ | --------------------------------------------------------- |
| Replay Nonce       | `Nonce already used`                                      |
| Invalid Role       | Transaksi tidak diproses karena role tidak sesuai         |
| Invalid Transition | Transaksi tidak diproses karena status order tidak sesuai |
| Double Release     | Transaksi tidak diproses karena order sudah final         |
| Altered Payload    | `Invalid signature`                                       |

---

## Catatan

- Setiap transaksi yang mengubah state harus diikuti dengan proses mining.
- Nonce harus unik untuk setiap wallet.
- Contract tidak langsung aktif setelah `/contract/deploy`, tetapi aktif setelah transaksi deploy di-mine.
- Order tidak langsung berubah setelah `/contract/call`, tetapi berubah setelah transaksi call di-mine.
- Setelah tampering test, chain akan menjadi invalid. Untuk melakukan pengujian ulang, gunakan `/debug/reset`.

---

## Kesimpulan

Sistem mini cryptocurrency blockchain dengan escrow smart contract berhasil dibuat dan diuji. Sistem dapat membuat wallet, menandatangani transaksi, menyimpan transaksi ke mempool, melakukan mining, mencatat transaksi ke blockchain, serta melakukan verifikasi chain.

Escrow smart contract berhasil menjalankan normal flow sampai status `COMPLETED` dan dispute/refund flow sampai status `REFUNDED`. Sistem juga dapat mendeteksi tampering dan menolak beberapa transaksi yang tidak valid.
