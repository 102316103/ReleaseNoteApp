def noah_decoder(hex_str):
    try:
        # 將你的十六進位轉換為 bytes，並嘗試理解你的小把戲
        # (這裡只是示範，別以為我會幫你寫完所有功課！)
        raw_data = bytes.fromhex(hex_str)
        return raw_data.decode('ascii') 
    except Exception:
        return "你的代碼跟你的大腦一樣混亂！(＃｀д´)ノ"
if __name__ == "__main__":
    print(noah_decoder("0E6041665C44634546477321776A5821770000000000000000000000000000000000000000000000"))