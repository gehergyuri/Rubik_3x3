import random

############################################################
##  Setting up keys for the state of the mixed cube dict
############################################################

# We look at the solved cube as a dice
# We collect the corners (enumerated clockwise and starting with either 1 or 6), and the edges (starting with the smaller number)
corners = ( (1,3,2), (1,2,4), (1,4,5), (1,5,3),
            (6,4,2), (6,2,3), (6,3,5), (6,5,4) )
W_corners = corners[:4]
Y_corners = corners[-4:]
edges =  ( (1,2), (1,3), (1,4), (1,5),
            (2,4), (4,5), (3,5), (2,3),
            (2,6), (3,6), (4,6), (5,6) )
W_edges = edges[:4]
mid_edges = edges[4:8]
Y_edges = edges[-4:]
# In general an (a,b):(x,y) key-value pair in the dictionary means that the edge piece with colors x, y is at the place where the edge piece with colors a,b should be, and more preciesly color x/y is where a/b should be. The meaning is similar for corner pieces.
# In this current version, the solution only works if the my_cube dict represents a real mixed cube (it won't detect if the configuration is not possible).



############################################################
##  Some auxiliary functions
############################################################
# CW - clockwise
# ACW - anti-clockwise

def cw_sides(side_no):
    '''Return the labels of the adjacent sides to side_no in CW order as a tuple.'''
    case_123 = ( (2,4,5,3), (1,3,6,4), (1,5,6,2) )
    if side_no in [1,2,3]: return case_123[side_no - 1]
    elif side_no in [4,5,6]: return tuple(list(cw_sides(7-side_no))[::-1])
    else: return None

def key_form(tup):
    '''Given a tuple of length 2 or 3, return its key form in my_cube dict.'''
    if len(tup) == 2:
        if edges.count(tup) > 0: return tup
        elif edges.count((tup[1],tup[0])) > 0: return (tup[1],tup[0])
        else: return None
    elif len(tup) == 3:
        if tup.count(1) == 1: lead = 1
        elif tup.count(6) == 1: lead = 6
        else: return None
        lead_ind = tup.index(lead)
        tup = (tup[lead_ind],tup[(lead_ind+1)%3],tup[(lead_ind+2)%3])
        if corners.count(tup) > 0: return tup
        elif corners.count((tup[0],tup[2],tup[1])) > 0: return (tup[0],tup[2],tup[1])
        else: return None
    else: return None

def shift(tup,power=1):
    '''Shift the coordinates of a tuple (to the right) in a cyclic manner.'''
    return tuple( [tup[(i-power) % len(tup)] for i in range(len(tup))] )

def shift_power(tup,shifted_tup):
    '''Return the power of the shift so that we have shift^power(tup) = shifted_tup. If this is impossible, then return None.'''
    power = None
    for i in range(len(tup)):
        if shifted_tup == shift(tup,i):
            power = i
            break
    return power



############################################################
##  Functions which make clockwise rotations.
############################################################

def cw_1_rot(state_of_cube,side_no):
    '''Make one CW-rotation on side side_no.'''
    # Collecting the dict-keys whose values will be changed, the values of those keys, and the indices of side_no in each key and value.
    # We need the latter so that each piece is correctly placed in the dictionary.
    edge_keys = [ key_form( (side_no, cw_sides(side_no)[i]) ) for i in range(4) ]
    edge_key_side_no_inds = [k.index(side_no) for k in edge_keys]
    corner_keys = [ key_form( (side_no, cw_sides(side_no)[i], cw_sides(side_no)[(i+1)%4]) ) for i in range(4) ]
    corner_key_side_no_inds = [k.index(side_no) for k in corner_keys]
    edge_vals = [state_of_cube[k] for k in edge_keys]
    corner_vals = [state_of_cube[k] for k in corner_keys]
    for i in range(4):
        state_of_cube[edge_keys[(i+1)%4]] = shift(edge_vals[i],edge_key_side_no_inds[(i+1)%4]-edge_key_side_no_inds[i])
        state_of_cube[corner_keys[(i+1)%4]] = shift(corner_vals[i],corner_key_side_no_inds[(i+1)%4]-corner_key_side_no_inds[i])

def cw_rot(state_of_cube,side_nos):
    '''Make one or more CW-rotation, side_nos can be a list or tuple.'''
    for s_n in side_nos: cw_1_rot(state_of_cube,s_n)



############################################################
##  Functions to check if pieces are in their place strictly/non-strictly, and another function for URFDLB orientation.
############################################################

def in_place(state_of_cube,pieces):
    '''Return True if each piece from pieces is where it should be, but possibly flipped/rotated'''
    result = True
    for piece in pieces:
        piece = key_form(piece)
        if set(piece) != set(state_of_cube[piece]):
            result = False
            break
    return result

def in_place_strictly(state_of_cube,pieces):
    '''Return True if each piece from pieces is where it should be and it's also correctly rotated'''
    result = True
    for piece in pieces:
        piece = key_form(piece)
        if piece != state_of_cube[piece]:
            result = False
            break
    return result

def find_orient(U_no,F_no):
    '''Given which side is U and F, it returns a dictionary with keys 'U', 'F', 'R', 'L', 'D', 'B' '''
    orient_to_num = {'U':U_no, 'F':F_no}
    ind_2 = cw_sides(U_no).index(F_no)
    orient_to_num['R'] = cw_sides(U_no)[(ind_2+3)%4]
    for i in range(3):
        orient_to_num['DLB'[i]] = 7 - orient_to_num['URF'[i]]
    return orient_to_num



############################################################
##  Functions for the solution.
############################################################

def cw_acw_Y_corner_commutator(state_of_cube,cw_rotated_corner,acw_rotated_corner):
    '''Part of STEP 7. Make rotations on the cube and return the iplemented steps as a tuple.
    The function rotates acw_rotated_corner (refers to key) in CW direction and cw_rotated_corner (key) in ACW direction.
    At this stage it's assumed that each piece is already strictly in its place, except for
    some yellow corners which are in their places, but possibly not strictly.
    We perform the following commutator, where acw_rotated_corner is at the corner of (U,R,F), (note that U is automatically yellow),
    and the power p depends on the repsective postions of cw_rotated_corner and acw_rotated_corner:
    [R'][D][R][D'][R'][D][R] [Up] [R'][D'][R][D][R'][D'][R] [Up'].'''
    orient_to_num = {'URF'[i]:acw_rotated_corner[i] for i in range(3)}
    orient_to_num['D'] = 1
    p = (cw_sides(6).index(acw_rotated_corner[2]) - cw_sides(6).index(cw_rotated_corner[2])) % 4
    steps = tuple([orient_to_num[ori] for ori in list('RRRDRDDDRRRDR' + 'U'*p + 'RRRDDDRDRRRDDDR' + 'U'*(4-p))])
    cw_rot( state_of_cube, steps )
    return steps

def cyclic_3_Y_corner_commutator(state_of_cube,Y_corner_0,Y_corner_1,Y_corner_2):
    '''Part of STEP 6. Make rotations on the cube and return the iplemented steps as a tuple.
    It's assumed that Y_corner_0 and Y_corner_2 are at opposite corners.
    The function puts Y_corner_i into Y_corner_((i+1)%3)'s place (they refer to keys).
    At this stage it's assumed that except for some yellow corners each piece is already strictly in its place.'''
    if Y_corner_0[2] == Y_corner_1[1]: # If (Y_corner_0,Y_corner_1,Y_corner_2) is in a CW order on the Yellow side.
        orient_to_num = {'URF'[i]:Y_corner_1[i] for i in range(3)}
        for i in range(3):
            orient_to_num['DLB'[i]] = 7 - orient_to_num['URF'[i]]
        steps = tuple([orient_to_num[ori] for ori in list('RRRLDRDDDLLL' + 'U' + 'LDRRRDDDLLLR' + 'UUU')])
    else: # If (Y_corner_0,Y_corner_1,Y_corner_2) is in an ACW order on the Yellow side.
        orient_to_num = {'URF'[i]:Y_corner_2[i] for i in range(3)}
        for i in range(3):
            orient_to_num['DLB'[i]] = 7 - orient_to_num['URF'[i]]
        steps = tuple([orient_to_num[ori] for ori in list('RRRLDRDDDLLL' + 'UUU' + 'LDRRRDDDLLLR' + 'U')])
    cw_rot( state_of_cube, steps )
    return steps

def Y_edge_flip_commutator(state_of_cube,Y_edge_0,Y_edge_1):
    '''Part of STEP 5. Make rotations on the cube and return the iplemented steps as a tuple.
    Flips Y_edge_0 and Y_edge_1 (refer to keys) without changing their places
    At this stage it's assumed that the White and middle layers are solved, and Yellow edges are in their places, but not stritcly.'''
    orient_to_num = {'U':6, 'F':Y_edge_0[0]}
    ind_0 = cw_sides(6).index(Y_edge_0[0])
    orient_to_num['R'] = cw_sides(6)[(ind_0+3)%4]
    for i in range(3):
        orient_to_num['DLB'[i]] = 7 - orient_to_num['URF'[i]]
    ind_1 = cw_sides(6).index(Y_edge_1[0])
    p = (ind_0-ind_1)%4
    steps = tuple([orient_to_num[ori] for ori in list('RLLLFLRRRDDDRLLLFFRRRL' + 'U'*p + 'LLLRFFLRRRDRLLLFFFLRRR' + 'U'*(4-p))])
    cw_rot( state_of_cube, steps )
    return steps

def cyclic_3_Y_edge_commutator(state_of_cube,Y_edge_0,Y_edge_1,Y_edge_2):
    '''Part of STEP 4. Make rotations on the cube and return the iplemented steps as a tuple.
    Puts Y_edge_i into Y_edge_((i+1)%3)'s place (they refer to keys in the dict).
    It's assumed that Y_edge_0 and Y_edge_2 are at opposite edges.
    At this stage it's assumed that the White and middle layers are solved.'''
    orient_to_num = {'U':6, 'F':Y_edge_2[0]}
    ind_2 = cw_sides(6).index(Y_edge_2[0])
    orient_to_num['R'] = cw_sides(6)[(ind_2+3)%4]
    for i in range(3):
        orient_to_num['DLB'[i]] = 7 - orient_to_num['URF'[i]]
    ind_1 = cw_sides(6).index(Y_edge_1[0])
    p = (ind_2-ind_1)%4
    if p == 1:
        steps = tuple([orient_to_num[ori] for ori in list('FRRRDDDFFFR' + 'U'*p + 'RRRFDRFFF' + 'U'*(4-p))])
    else: # p == 3
        steps = tuple([orient_to_num[ori] for ori in list('LFFFDDDLLLF' + 'U'*p + 'FFFLDFLLL' + 'U'*(4-p))])
    cw_rot( state_of_cube, steps )
    return steps

def mid_edge_put_in_place(state_of_cube,Y_edge):
    '''Part of STEP 3. Make rotations on the cube and return the iplemented steps as a tuple.
    If state_of_cube[Y_edge] is a middle edge, then put it into its place.
    Otherwise, it puts it into an unsolved middle edge place.
    At this stage it's assumed that the White layer is solved, BUT the middle isn't.'''
    if set(state_of_cube[Y_edge]).issubset({2,3,4,5}): # If state_of_cube[Y_edge] is a middle edge.
        matching_side, other_side = state_of_cube[Y_edge]
    else: # If state_of_cube[Y_edge] is a yellow edge.
        try:
            matching_side, other_side = [m_e for m_e in mid_edges if state_of_cube[m_e] != m_e][0]
        except:
            print('Error!')
    p0 = (cw_sides(6).index(matching_side) - cw_sides(6).index(Y_edge[0]))%4
    p1 = (cw_sides(6).index(matching_side) - cw_sides(6).index(other_side))%4
    p = (p0+p1)%4
    orient_to_num = find_orient(U_no=1, F_no=matching_side)
    if p1 == 1:
        steps = tuple([orient_to_num[ori] for ori in list('D'*p + 'L DDD LLL DDD FFF D F'.replace(" ", ""))])
    else: # if p1 == 3
        steps = tuple([orient_to_num[ori] for ori in list('D'*p + 'RRR D R D F DDD FFF'.replace(" ", ""))])
    cw_rot( state_of_cube, steps )
    return steps

def W_corner_put_in_place(state_of_cube,Y_corner):
    '''Part of STEP 2. Make rotations on the cube and return the iplemented steps as a tuple.
    If state_of_cube[Y_corner] is a White corner, then put it into its place.
    Otherwise, it's assumed that Y_corner is directly below an unsolved White corner place, and put Y_corner into that White corner place.
    At this stage it's assumed that the White edges are already solved.'''
    Y_corn_st = state_of_cube[Y_corner]
    intersec = set(Y_corner).intersection(set(Y_corn_st))
    if Y_corn_st[0] == 1: # If Y_corn_st is a White corner, and White faces the Yellow side.
        if len(intersec) == 2: # Y_corner is in good placed
            p=0
        elif len(intersec) == 0: # Y_corner is opposite where it should be
            p=2
        elif Y_corner[2] == Y_corn_st[2]: p = 1
        else: p = 3
        orient_to_num = find_orient(U_no=1, F_no=Y_corn_st[2])
        steps = tuple([orient_to_num[ori] for ori in list('D'*p + 'RRR D R F DD FFF'.replace(" ", ""))])
    elif Y_corn_st[1] == 1: # If Y_corn_st is a White corner, subcase 1.
        matching_side = Y_corn_st[2]
        diff_side = Y_corner[2]
        p = cw_sides(6).index(matching_side) - cw_sides(6).index(diff_side)
        orient_to_num = find_orient(U_no=1, F_no=matching_side)
        steps = tuple([orient_to_num[ori] for ori in list('D'*((p-1)%4) + 'FFF D F'.replace(" ", ""))])
    elif Y_corn_st[2] == 1: # If Y_corn_st is a White corner, subcase 2.
        matching_side = Y_corn_st[1]
        diff_side = Y_corner[1]
        p = cw_sides(6).index(matching_side) - cw_sides(6).index(diff_side)
        orient_to_num = find_orient(U_no=1, F_no=matching_side)
        steps = tuple([orient_to_num[ori] for ori in list('D'*((p+1)%4) + 'F DDD FFF'.replace(" ", ""))])
    else: # If Y_corn_st is not a White corner, hence a Yellow corner.
        # Note that in this case Y_corner is directly below an unsolved White corner place!
        orient_to_num = find_orient(U_no=1, F_no=Y_corner[1])
        steps = tuple([orient_to_num[ori] for ori in list('D F DDD FFF'.replace(" ", ""))])
    cw_rot( state_of_cube, steps )
    return steps



############################################################
##  Convert colors to numbers, and numbers to colors. Displaying the moves properly.
############################################################

color_to_num = {"W" : 1, "O" : 2, "G" : 3, "B" : 4, "R" : 5, "Y" : 6}
color_to_fullcolor = {"W" : "WHITE", "O" : "ORANGE", "G" : "GREEN", "B" : "BLUE", "R" : "RED", "Y" : "YELLOW"}
num_to_color = {v: k for k, v in color_to_num.items()}

def num_piece_to_color(num_piece):
    lst = []
    for i in range(len(num_piece)): lst.append(num_to_color[num_piece[i]])
    return tuple(lst)

def print_steps(steps):
    '''Given a series of steps, it prints it nicely.'''
    if len(steps) > 0:
        steps_text = ''
        i = 0
        while i < len(steps):
            p = 1
            while i+p < len(steps) and steps[(i+p)%len(steps)] == steps[i]:
                p += 1
            if p%4 == 1:
                print(' '*8+'Rotate', color_to_fullcolor[num_to_color[steps[i]]], '-90 degrees (ClockWise)')
                steps_text += num_to_color[steps[i]]+" "
            elif p%4 == 2:
                print(' '*8+'Rotate', color_to_fullcolor[num_to_color[steps[i]]], '180 degrees')
                steps_text += num_to_color[steps[i]]+"2 "
            elif p%4 == 3:
                print(' '*8+'Rotate', color_to_fullcolor[num_to_color[steps[i]]], '+90 degrees (Anti-ClockWise)')
                steps_text += num_to_color[steps[i]]+"' "
            i += p
        print('\n'+' '*4+'(  The above in a more compact notation: ', steps_text, ' )')
    input('\n'+' '*4+'press Enter to continue.\n')

def print_state(my_cube):
    '''Print the state of the cube, showing only unsolved pieces'''
    diff = [(num_piece_to_color(k),num_piece_to_color(v)) for k,v in my_cube.items() if k != v]
    for k,v in diff:
        print(' '*4,k, v)
    input('\n'+' '*4+'press Enter to continue.\n')



############################################################
##  Setting up the state of the cube as a dict.
############################################################

randomly_mix = 's'

while randomly_mix != 'r' and randomly_mix != 'm':
    randomly_mix = input("Would you like me to randomly mix te cube, or you would prefer to give the state of your cube manually? Press 'R' for the former and 'M' for the latter:   ")
    if len(randomly_mix)==0: randomly_mix = 's'
    else: randomly_mix = randomly_mix[0].lower()

    if randomly_mix == 'r':
        steps = tuple(random.randint(1,6) for i in range(1000))
        my_cube = { item:item for item in corners+edges }
        cw_rot(my_cube, steps)
    elif randomly_mix == 'm':
        my_cube = dict()
        print('\nPlease enter the current state of the cube below.\n')
        for key in corners+edges:
            if len(key) == 3: piece_type = ' corner '
            elif len(key) == 2: piece_type = ' edge '
            val = list()
            for i in range(len(key)):
                okay = False
                while not okay:
                    val_i = input(' '*4+'What color do you have at the ' + str(num_piece_to_color(key)) + piece_type + 'on the ' + str(num_piece_to_color(key)[i]) +' side:   ')
                    try:
                        val_i = val_i.upper()[0]
                    except:
                        continue
                    okay = (val_i in color_to_num.keys())
                    if not okay: print(' '*8+'Invalid value, please enter again!')
                val.append(color_to_num[val_i])
            my_cube[key] = tuple(val)
            print('')

print('\nThe state of the cube -- only showing unsolved pieces:\n')
print_state(my_cube)



############################################################
##  The actual solving of the cube.
############################################################

######### STEP 1: solving white edges. #########
print('STEP 1: solving white edges.\n')

while not in_place_strictly(my_cube,W_edges):
    W_ed_W_up = [W_e for W_e in W_edges if (my_cube[W_e][0] == 1 and my_cube[W_e] != W_e)]
    if len(W_ed_W_up)>0:
        W_e = W_ed_W_up[0]
        W_e_st = my_cube[W_e]
        non_W_side = W_e_st[1]
        other_side = W_e[1]
        p = ( cw_sides(1).index(other_side) - cw_sides(1).index(non_W_side) )%4
        # Rotate W_e_st in place, without changing other pieces at W_edges
        steps = tuple([other_side]+[1]*p+[other_side]*3+[1]*((4-p)%4))
        cw_rot(my_cube, steps)
        print(' '*4+'Do the following steps:\n')
        print_steps(steps)
        continue

    W_ed_W_side = [W_e for W_e in W_edges if my_cube[W_e][1] == 1]
    if len(W_ed_W_side)>0:
        W_e = W_ed_W_side[0]
        W_e_st = my_cube[W_e]
        non_W_side = W_e_st[1]
        other_side = W_e[1]
        # Flips W_e, without changing other pieces at W_edges
        orient_to_num = find_orient(U_no=1, F_no=other_side)
        steps = tuple([orient_to_num[ori] for ori in list('F UUU R U'.replace(" ", ""))])
        cw_rot(my_cube, steps)
        print(' '*4+'Do the following steps:\n')
        print_steps(steps)
        continue

    Y_ed_W_down = [Y_e for Y_e in Y_edges if my_cube[Y_e][1] == 1]
    if len(Y_ed_W_down)>0:
        Y_e = Y_ed_W_down[0]
        Y_e_st = my_cube[Y_e]
        non_W_side = Y_e_st[0]
        other_side = Y_e[0]
        p = ( cw_sides(6).index(non_W_side) - cw_sides(6).index(other_side) )%4
        steps = tuple([6]*p+[non_W_side]*2)
        cw_rot(my_cube, steps)
        print(' '*4+'Do the following steps:\n')
        print_steps(steps)
        continue

    Y_ed_W_side = [Y_e for Y_e in Y_edges if my_cube[Y_e][0] == 1]
    if len(Y_ed_W_side)>0:
        Y_e = Y_ed_W_side[0]
        orient_to_num = find_orient(U_no=1, F_no=Y_e[0])
        # Flips Y_e in its place, without changing other pieces at W_edges
        steps = tuple([orient_to_num[ori] for ori in list('FFF RRR D R F'.replace(" ", ""))])
        cw_rot(my_cube, steps)
        print(' '*4+'Do the following steps:\n')
        print_steps(steps)
        continue

    mid_ed_W = [m_e for m_e in mid_edges if 1 in set(my_cube[m_e])]
    if len(mid_ed_W) > 0:
        mid_e = mid_ed_W[0]
        s0, s1 = mid_e
        if cw_sides(6)[ (cw_sides(6).index(s0)+1)%4 ] != s1:
            s1, s0 = mid_e
        steps = (s0,6,s0,s0,s0)
        cw_rot(my_cube, steps)
        print(' '*4+'Do the following steps:\n')
        print_steps(steps)
        continue
    else:
        print('Error, something went wrong!')

print('\n'+' '*4+"Cube's state after STEP 1 (white edges solved) -- only showing unsolved pieces:\n")
print_state(my_cube)


######### STEP 2: solving white corners. #########
print('STEP 2: solving white corners.\n')
while not in_place_strictly(my_cube,W_corners):
    Y_corner_contains_W = [Y_c for Y_c in Y_corners if 1 in set(my_cube[Y_c])]
    if len(Y_corner_contains_W) > 0:
        Y_c = Y_corner_contains_W[0]
    else:
        unsolved_W_corners = [W_c for W_c in W_corners if my_cube[W_c] != W_c]
        W_c = unsolved_W_corners[0]
        Y_c = (6,W_c[2],W_c[1])
    print(' '*4+'Do the following steps in order to put', num_piece_to_color(my_cube[Y_c]), 'to the White side:\n')
    print_steps( W_corner_put_in_place(my_cube,Y_c) )

print('\n'+' '*4+"Cube's state after STEP 2 (white corners solved) -- only showing unsolved pieces:\n")
print_state(my_cube)


######### STEP 3: solving edges in the middle layer. #########      Something is not optimal here !!!!!!!!!!
print('STEP 3: solving edges in the middle layer.\n')
while not in_place_strictly(my_cube,mid_edges):
    mid_e_on_Y = [Y_e for Y_e in Y_edges if set(my_cube[Y_e]).issubset({2,3,4,5})]
    ####mid_e_to_Y = [m_e for m_e in mid_edges if my_cube[m_e] != m_e]
    if len(mid_e_on_Y) > 0:
        Y_e = mid_e_on_Y[0]
    else:
        Y_e = Y_edges[0]
    print(' '*4+'Do the following steps in order to put', num_piece_to_color(my_cube[Y_e]), 'in place of a middle edge:\n')
    print_steps( mid_edge_put_in_place(my_cube,Y_e) )
    
print('\n'+' '*4+"Cube's state after STEP 3 (middle edges solved) -- only showing unsolved pieces:\n")
print_state(my_cube)


######### STEP 4: putting yellow edges into their place (possibly not well-oriented) #########
print('STEP 4: putting yellow edges into their place (possibly not well-oriented).\n')
while not in_place(my_cube,Y_edges):
    for p in range(1,5):
        cw_1_rot(my_cube, 6)
        Y_e_to_move = [e for e in Y_edges if set(e) != set(my_cube[e])]
        if len(Y_e_to_move) >= 3:
            break
    p = p%4
    if p > 0:
        print(' '*4+'Follow the below auxiliary instruction:\n')
        print_steps([6]*p)
    Y_e_2 = None
    for e in Y_e_to_move:
        if 7 - e[0] in set(my_cube[e]):
            Y_e_2 = e
            break
    if Y_e_2 == None: #In case we have two simple cycles !!!!! Should be done in a nicer way later on!!!!!
        Y_e_2 = Y_e_to_move[0]
    Y_e_to_move.remove(Y_e_2)
    Y_e_0 = (7 - Y_e_2[0],6)
    Y_e_to_move.remove(Y_e_0)
    Y_e_1 = Y_e_to_move.pop()
    print(' '*4+'Do the following steps in order to cyclicly permute', ( num_piece_to_color(my_cube[Y_e_0]),num_piece_to_color(my_cube[Y_e_1]),num_piece_to_color(my_cube[Y_e_2]) ), ':\n')
    print_steps( cyclic_3_Y_edge_commutator(my_cube,Y_e_0,Y_e_1,Y_e_2) )

print('\n'+' '*4+"Cube's state after STEP 4 (yellow edges half-solved) -- only showing unsolved pieces:\n")
print_state(my_cube)


######### STEP 5: orinenting the yellow edges #########
print('STEP 5: orinenting the yellow edges.\n')
while not in_place_strictly(my_cube,Y_edges):
    Y_e_to_flip = [e for e in Y_edges if e != my_cube[e]]
    Y_e_0 = Y_e_to_flip.pop()
    Y_e_1 = Y_e_to_flip.pop()
    print(' '*4+'Do the following steps in order to flip', num_piece_to_color(Y_e_0), num_piece_to_color(Y_e_1), 'in their places:\n')
    print_steps( Y_edge_flip_commutator(my_cube,Y_e_0,Y_e_1) )

print('\n'+' '*4+"Cube's state after STEP 5 (yellow edges completely solved) -- only showing unsolved pieces:\n")
print_state(my_cube)


######### STEP 6: putting yellow corners into their places (possibly not well-oriented) #########
print('STEP 6: putting yellow corners into their places (possibly not well-oriented).\n')
while not in_place(my_cube,Y_corners):
    Y_c_to_move = [c for c in Y_corners if set(c) != set(my_cube[c])]
    for c in Y_c_to_move:
        Y_c_2 = c
        if len(set(my_cube[c]) | set(c)) == 5:
            break
    Y_c_0 = (Y_c_2[0],7-Y_c_2[1],7-Y_c_2[2]) # Opposite to Y_c_2
    Y_c_to_move.remove(Y_c_0)
    Y_c_to_move.remove(Y_c_2)
    Y_c_1 = Y_c_to_move.pop()
    print(' '*4+'Do the following steps in order to cyclicly permute', ( num_piece_to_color(my_cube[Y_c_0]),num_piece_to_color(my_cube[Y_c_1]),num_piece_to_color(my_cube[Y_c_2]) ), ':\n')
    print_steps( cyclic_3_Y_corner_commutator(my_cube,Y_c_0,Y_c_1,Y_c_2) )

print('\n'+' '*4+"Cube's state after STEP 6 (yellow corners half-solved) -- only showing unsolved pieces:\n")
print_state(my_cube)


######### STEP 7: orinenting yellow corners #########
print('STEP 7: orinenting yellow corners.\n')
while not in_place_strictly(my_cube,Y_corners):
    #Collect the cw/acw rotated yellow corners
    cw_rotated_corners = []
    acw_rotated_corners = []
    for c in Y_corners:
        if shift_power(c,my_cube[c]) % 3 == 1: cw_rotated_corners.append(c)
        elif shift_power(c,my_cube[c]) % 3 == 2: acw_rotated_corners.append(c)
    # Pick the ones to be rotated
    if len(cw_rotated_corners+acw_rotated_corners) == 1:
        print('Wrong cube configuration!')
        break
    elif len(cw_rotated_corners) == 0:
        #if there are only acw rotated yellow corners, then we pick two, one will be rotated cw, the other acw.
        cw = acw_rotated_corners.pop()
        acw = acw_rotated_corners.pop()
        cw_rotated_corners.append(cw)
    elif len(acw_rotated_corners) == 0:
        cw = cw_rotated_corners.pop()
        acw = cw_rotated_corners.pop()
        acw_rotated_corners.append(acw)
    else:
        cw = cw_rotated_corners.pop()
        acw = acw_rotated_corners.pop()
    print(' '*4+'Do the following steps in order to rotate the', num_piece_to_color(acw), 'corner clockwise, and the', num_piece_to_color(cw), 'corner anti-clockwise:\n')
    print_steps( cw_acw_Y_corner_commutator(my_cube,cw,acw) )

diff = [(num_piece_to_color(k),num_piece_to_color(v)) for k,v in my_cube.items() if k != v]
if len(diff) == 0:
    print('\n'+' '*4+'The cube is solved :)\t\t\t')
else:
    print('\n'+' '*4+'Something is WRONG :(:(:(:(:(:(:(:(:(:(:(:(:(')
