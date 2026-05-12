from PIL import Image
import os
import sys
# sys.set_int_max_str_digits(10000000)
import lzma

def compress_lzma(data_bytes):
    return lzma.compress(data_bytes)

def decompress_lzma(data_bytes):
    return lzma.decompress(data_bytes)

def load_bmp(path): #функция для загрузки изображения
    img = Image.open(path) #просто открывает файл

    img = img.convert("RGB") #приводит картинку к формату RGB 

    width, height = img.size #получает ширину и высоту
    pixels = list(img.getdata())  # получает массив пикселей вида [(R,G,B), (R,G,B), ...]

    return width, height, pixels

def save_bmp(path, width, height, pixels): #функция для восстановления исходного изображения по массиву пикселей
    img = Image.new("RGB", (width, height)) #создание пустого изображения с палитрой RGB и такого же размера как исходное
    img.putdata(pixels) #вставка пикселей
    img.save(path) #сохранение изображения

def compare_images_pixels(path1, path2): #сравнение исходного и восстановленного изображения по массивам пикселей для предотвращения ошибок
    img1 = Image.open(path1).convert("RGB")
    img2 = Image.open(path2).convert("RGB")

    pixels1 = list(img1.getdata())
    pixels2 = list(img2.getdata())

    if len(pixels1) != len(pixels2): #если размеры не совпадают значит массив пикселей не правильный
        return False

    for i in range(len(pixels1)): 
        if pixels1[i] != pixels2[i]:
            print("Разница в пикселе", i, pixels1[i], pixels2[i])
            return False

    return True

def build_palette(pixels): #создание палитры уникальных цветов и карты индексов
    palette = []          # уникальные цвета
    palette_map = {}      # цвет: индекс
    indices = []          # список индексов

    for pixel in pixels:
        if pixel not in palette_map:
            palette_map[pixel] = len(palette)
            palette.append(pixel)

        indices.append(palette_map[pixel])

    return palette, indices

def restore_pixels(palette, indices): #обратно из карты индексов в пиксели
    return [palette[i] for i in indices]


def split_into_blocks(indices, width, height, block_size): #разделение на блоки
    blocks = []

    for by in range(0, height, block_size):
        for bx in range(0, width, block_size):
            block = []

            for y in range(block_size):
                for x in range(block_size):
                    ix = bx + x
                    iy = by + y

                    if ix < width and iy < height:
                        index = iy * width + ix
                        block.append(indices[index])
                    else:
                        block.append(0)

            blocks.append(block)

    return blocks

def merge_blocks(blocks, width, height, block_size): #обратно из блоков в индексы
    indices = [0] * (width * height)

    block_idx = 0

    for by in range(0, height, block_size):
        for bx in range(0, width, block_size):
            block = blocks[block_idx]
            block_idx += 1

            i = 0
            for y in range(block_size):
                for x in range(block_size):
                    ix = bx + x
                    iy = by + y

                    if ix < width and iy < height:
                        index = iy * width + ix
                        indices[index] = block[i]

                    i += 1

    return indices



def build_block_dictionary(blocks):
    unique_blocks = []        # список уникальных блоков
    block_map = {}            # блок: индекс
    block_indices = []        # последовательность индексов

    for block in blocks:
        key = tuple(block)

        if key not in block_map:
            block_map[key] = len(unique_blocks)
            unique_blocks.append(block)

        block_indices.append(block_map[key])

    return unique_blocks, block_indices

def restore_blocks(unique_blocks, block_indices):
    return [unique_blocks[i] for i in block_indices]


def rank_block(block, k): #ранжирование блоков
    r = 0
    M = len(block)

    for i in range(M):
        r = r * k + block[i]

    return r

def unrank_block(r, k, M):
    block = [0] * M

    for i in range(M - 1, -1, -1):
        block[i] = r % k
        r //= k

    return block

def int_to_bytes(n, k, m):
    rmax = (k ** m) - 1
    byte_length = (rmax.bit_length() + 7) // 8
    return n.to_bytes(byte_length, 'big')

if __name__ == "__main__":
    w, h, pixels = load_bmp("image.bmp")
    #save_bmp("test_output.bmp", w, h, pixels)
    #if compare_images_pixels("image.bmp", "test_output.bmp"):
    #    os.remove("test_output.bmp")
    print("Размер:", w, "x", h)
    #    print("Первый пиксель:", pixels[0])

    palette, indices = build_palette(pixels)

    print("Количество пикселей:", len(pixels))
    print("Размер палитры:", len(palette))

    #    restored = restore_pixels(palette, indices)
    #    print("Совпадает ли индексы:", restored == pixels)
    m = 4
    blocks = split_into_blocks(indices, w, h, m)
    #    restored_indices = merge_blocks(blocks, w, h, 8)
    #    print("Совпадает:", restored_indices == indices)
    #    print("Количество блоков:", len(blocks))
    #    print("Первый блок:", blocks[0])



    #    blocks = split_into_blocks(indices, w, h, 4)

    #unique_blocks, block_indices = build_block_dictionary(blocks)

    print("Всего блоков:", len(blocks))
    #    print("Уникальных блоков:", len(unique_blocks))
    #    print("Первые индексы:", block_indices[:10])
    #    restored_blocks = restore_blocks(unique_blocks, block_indices)
    #    print("Совпадает:", restored_blocks == blocks)

    k = len(palette)
    block_ranks = [rank_block(block, k) for block in blocks]
    #    print("Первые ранги:", block_ranks[:5])


    #U = len(unique_blocks)
    #T = len(block_indices)
    #R = rank_sequence(block_indices, U)
        # print("Итоговый ранг:", R) 


    original_size = os.path.getsize("image.bmp")
    print("Размер исходного BMP:", original_size, "байт")
    data = [int_to_bytes(r, k, m ** 2) for r in block_ranks]
    R_size = len(data[0]) * len(data)
    print(data[0], len(data[0]))
    print("Размер R:", R_size, "байт")
    palette_size = k * 3
    print("Размер палитры:", palette_size, "байт")
    #    block_size_pixels = len(unique_blocks[0])
    #    blocks_size = len(unique_blocks) * block_size_pixels
    #    print("Размер уникальных блоков:", blocks_size, "байт")
    total_size = R_size + palette_size #+ blocks_size
    print("Общий размер:", total_size, "байт")
    compression_ratio = original_size / total_size
    print("Коэффициент сжатия:", compression_ratio)
    #else:
    #    print("Неправильное преобразование изображения")