import pymysql

def fix():
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='12345',
            database='liqui_sense'
        )
        cur = conn.cursor()
        
        # 1. Sign Correction for all users based on keywords
        keywords = ['sales', 'income', 'deposit', 'interest', 'refund', 'credit', 'received']
        total_signed = 0
        for kw in keywords:
            # Positive for credits
            affected = cur.execute(f"UPDATE transactions SET amount = ABS(amount) WHERE (LOWER(raw_text) LIKE '%{kw}%' OR LOWER(counterparty) LIKE '%{kw}%') AND amount < 0")
            total_signed += affected
            # Negative for everything else (safety check)
            # Actually better to just focus on ensuring credits are positive
            
        # 2. Re-extract amount if we have raw_text with pipes
        cur.execute("SELECT id, raw_text FROM transactions WHERE raw_text LIKE '%|%'")
        rows = cur.fetchall()
        total_extracted = 0
        for rid, raw_text in rows:
            parts = [p.strip() for p in raw_text.split('|')]
            nums = []
            for p in parts:
                try:
                    clean = p.replace('₹','').replace('$','').replace(',','').strip()
                    f = float(clean)
                    nums.append(f)
                except:
                    continue
            
            if len(nums) >= 2:
                real_amount_val = nums[-2] # One before balance
                is_credit = any(k in raw_text.lower() for k in keywords)
                real_amount = real_amount_val if is_credit else -real_amount_val
                cur.execute("UPDATE transactions SET amount = %s WHERE id = %s", (real_amount, rid))
                total_extracted += 1

        conn.commit()
        print(f"Migration completed. Signed {total_signed} and Extracted {total_extracted} rows.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    fix()
