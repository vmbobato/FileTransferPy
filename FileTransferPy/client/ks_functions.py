def encrypt_ks(msg, public_key):
    num_char = []
    bin_list = []
    mult_list = []
    cypher = []
    for i in msg:
        num_char.append(ord(i))
    for num in num_char:
        bin_num = format(num, 'b')
        if len(bin_num) < 8:
            bin_reversed = bin_num[::-1]
            while True:
                bin_reversed += "0"
                if len(bin_reversed) == 8:
                    break
            bin_num = bin_reversed[::-1]
        bin_list.append(bin_num)
    for binary in bin_list:
        i = 0
        for digit in binary:
            num = int(digit) * public_key[i]
            i += 1
            mult_list.append(num)
        sum_list = sum(mult_list)
        mult_list = []
        cypher.append(sum_list)
    new_one = []
    for value in cypher:
        new_one.append(str(value))
    string_cypher = '<sep>'.join(new_one)
    return string_cypher


def decrypt_ks(cypher, private_key, inverse_n, m_value):
    bin_list = []
    bitstring = ''
    inter_text = []
    plaintext = []
    reversed_priv_key = private_key[::-1]
    cypher = cypher.split("<sep>")
    for num in cypher:
        if num != '':
            inter_text.append((int(num)*inverse_n) % m_value)
    for num in inter_text:
        for value in reversed_priv_key:
            if num < value:
                bitstring += "0"
            else:
                bitstring += "1"
                num -= value
        bitstring = bitstring[::-1]
        bin_list.append(bitstring)
        bitstring = ''
    for bin in bin_list:
        number = int(bin, 2)
        plaintext.append(chr(number))
    return ''.join(plaintext)

