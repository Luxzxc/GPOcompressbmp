import lzma
import os
import struct
from PIL import Image

# --- Существующие функции из вашего кода ---

def load_bmp(path):
    img = Image.open(path).convert("RGB")
    width, height = img.size
    pixels = list(img.getdata())
    return width, height, pixels

def save_bmp(path, width, height, pixels):
    img = Image.new("RGB", (width, height))
    img.putdata(pixels)
    img.save(path)

def build_palette(pixels):
    palette = []
    palette_map = {}
    indices = []
    for pixel in pixels:
        if pixel not in palette_map:
            palette_map[pixel] = len(palette)
            palette.append(pixel)
        indices.append(palette_map[pixel])
    return palette, indices

def split_into_blocks(indices, width, height, block_size):
    blocks = []
    for by in range(0, height, block_size):
        for bx in range(0, width, block_size):
            block = []
            for y in range(block_size):
                for x in range(block_size):
                    ix, iy = bx + x, by + y
                    if ix < width and iy < height:
                        block.append(indices[iy * width + ix])
                    else:
                        block.append(0)
            blocks.append(block)
    return blocks

def rank_block(block, k):
    r = 0
    for val in block:
        r = r * k + val
    return r

# --- НОВЫЕ ФУНКЦИИ ДЛЯ РАСЖАТИЯ ---

def unrank_block(r, k, m_sq):
    """Обратное преобразование числа (ранга) в блок индексов."""
    block = []
    for _ in range(m_sq):
        block.append(r % k)
        r //= k
    return block[::-1]  # Разворачиваем, так как при ранжировании умножали с конца

def merge_blocks(blocks, width, height, block_size):
    """Сборка индексов из блоков обратно в полотно изображения."""
    indices = [0] * (width * height)
    block_idx = 0
    for by in range(0, height, block_size):
        for bx in range(0, width, block_size):
            block = blocks[block_idx]
            block_idx += 1
            i = 0
            for y in range(block_size):
                for x in range(block_size):
                    ix, iy = bx + x, by + y
                    if ix < width and iy < height:
                        indices[iy * width + ix] = block[i]
                    i += 1
    return indices

def decompress_image(compressed_path, output_bmp):
    """Полный цикл восстановления из кастомного формата."""
    with open(compressed_path, "rb") as f:
        # Читаем метаданные
        w, h, k, m = struct.unpack(">IIII", f.read(16))
        # Читаем палитру
        palette_data = f.read(k * 3)
        palette = [tuple(palette_data[i:i+3]) for i in range(0, len(palette_data), 3)]
        # Читаем остальное (сжатые ранги)
        compressed_payload = f.read()
        
    # Разжимаем LZMA и восстанавливаем ранги
    raw_ranks = lzma.decompress(compressed_payload)
    
    # Определяем размер одного ранга в байтах
    rmax = (k ** (m**2)) - 1
    byte_len = (rmax.bit_length() + 7) // 8
    
    block_ranks = []
    for i in range(0, len(raw_ranks), byte_len):
        rank = int.from_bytes(raw_ranks[i:i+byte_len], 'big')
        block_ranks.append(rank)
        
    # Восстанавливаем блоки -> индексы -> пиксели
    blocks = [unrank_block(r, k, m**2) for r in block_ranks]
    indices = merge_blocks(blocks, w, h, m)
    pixels = [palette[i] for i in indices]
    
    save_bmp(output_bmp, w, h, pixels)
    print(f"Файл восстановлен в: {output_bmp}")

# --- ОБНОВЛЕННЫЙ MAIN ---

if __name__ == "__main__":
    INPUT_FILE = "test.bmp"
    COMPRESSED_FILE = "compressed.dat"
    RESULT_FILE = "restored.bmp"
    
    if not os.path.exists(INPUT_FILE):
        print(f"Положите файл {INPUT_FILE} в папку с кодом!")
    else:
        # 1. Сжатие
        w, h, pixels = load_bmp(INPUT_FILE)
        palette, indices = build_palette(pixels)
        m = 4
        k = len(palette)
        blocks = split_into_blocks(indices, w, h, m)
        block_ranks = [rank_block(b, k) for b in blocks]
        
        # Подготовка данных для записи
        rmax = (k ** (m**2)) - 1
        byte_len = (rmax.bit_length() + 7) // 8
        ranks_bytes = b"".join([r.to_bytes(byte_len, 'big') for r in block_ranks])
        compressed_ranks = lzma.compress(ranks_bytes) # Реальное сжатие
        
        # Запись своего формата файла (.dat)
        with open(COMPRESSED_FILE, "wb") as f:
            f.write(struct.pack(">IIII", w, h, k, m)) # Заголовок
            for color in palette:
                f.write(bytes(color)) # Палитра
            f.write(compressed_ranks) # Данные
            
        print(f"Сжато! Исходный: {os.path.getsize(INPUT_FILE)} байт, Сжатый: {os.path.getsize(COMPRESSED_FILE)} байт")

        original_size = os.path.getsize(INPUT_FILE)
        compressed_size = os.path.getsize(COMPRESSED_FILE)

        # Расчет коэффициентов
        compression_ratio = original_size / compressed_size
        compression_percentage = (1 - (compressed_size / original_size)) * 100

        print(f"--- Результаты сжатия ---")
        print(f"Исходный размер: {original_size} байт")
        print(f"Сжатый размер: {compressed_size} байт")
        print(f"Коэффициент сжатия (Ratio): {compression_ratio:.2f}")
        print(f"Эффективность (Savings): {compression_percentage:.2f}%")
        
        # 2. Расжатие
        decompress_image(COMPRESSED_FILE, RESULT_FILE)