def print_board(bo):
    for i in range(len(bo)):
        if i % 3 == 0 and i != 0:
            print("- - - - - - - - - - - - - ")

        for j in range(len(bo[0])):
            if j % 3 == 0 and j != 0:
                print(" | ", end="")

            if j == 8:
                print(bo[i][j])
            else:
                print(str(bo[i][j]) + " ", end="")

def is_valid(bo, r, c, num):
    # Dò lỗi trùng hàng ngang
    for i in range(9):
        if bo[r][i] == num and c != i:
            return False

    # Dò lỗi trùng hàng dọc
    for i in range(9):
        if bo[i][c] == num and r != i:
            return False

    # Dò lỗi trùng khối 3x3
    box_x = c // 3
    box_y = r // 3

    for i in range(box_y*3, box_y*3 + 3):
        for j in range(box_x * 3, box_x*3 + 3):
            if bo[i][j] == num and (i,j) != (r, c):
                return False

    return True

def solve(bo):
    """
    Thuật toán Iterative Backtracking (Không dùng đệ quy)
    Tìm vị trí trống, dùng Stack lưu vết. Giúp tốc độ giải vượt trội 
    và loại bỏ 100% nguy cơ Recursion Depth.
    """
    # Lấy tọa độ các ô tính toán
    empty_cells = []
    for i in range(9):
        for j in range(9):
            if bo[i][j] == 0:
                empty_cells.append((i, j))
                
    curr = 0 # Con trỏ đang đứng ở ô trống nào
    while 0 <= curr < len(empty_cells):
        r, c = empty_cells[curr]
        start_val = bo[r][c] + 1
        found = False
        
        # Thử số từ val hiện hành đến 9
        for val in range(start_val, 10):
            if is_valid(bo, r, c, val):
                bo[r][c] = val
                found = True
                break
                
        if found:
            # Đi tới ô trống tiếp theo (Push)
            curr += 1
        else:
            # Không có số khả thi, xé bài đi lùi (Trường hợp Backtrack)
            bo[r][c] = 0
            curr -= 1
            
    # Kiểm tra xem có đi hết toàn bộ lưới bài không
    return curr == len(empty_cells)
