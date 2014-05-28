:- modeh(1, serve_coffee(-space)).
:- modeb(1, pickup(+space, -int)).
:- modeb(1, putdown(+space, -int)).
:- modeb(1, con(+space, -int)).
:- modeb(3, dis(+num, -int)).
:- modeb(3, meetsdis(+int, +int)).
:- modeb(3, overlaps(+int, +int)).
:- modeb(3, during(+int, +int)).

serve_coffee(obj(area(seating_area(saw1)),obj(furniture(table1))).
dis(obj(area(manipulation_area(mae3))),obj(robot(trixi)),int(1,16)).
dis(obj(area(manipulation_area(mae3))),obj(robot(trixi)),int(43,417)).
dis(obj(kitchen_ware(mug(mug1))),obj(robot(trixi)),int(1,417)).
dis(obj(area(manipulation_area(mas1))),obj(robot(trixi)),int(1,54)).
dis(obj(kitchen_ware(mug(mug1))),obj(person(guest1)),int(1,72)).
dis(obj(kitchen_ware(mug(mug1))),obj(person(guest1)),int(74,417)).
con(obj(area(manipulation_area(mae3))),obj(robot(trixi)),int(17,42)).
con(obj(area(manipulation_area(mas1))),obj(robot(trixi)),int(55,417)).
con(obj(kitchen_ware(mug(mug1))),obj(person(guest1)),int(73,73)).
pickup(obj(kitchen_ware(mug(mug1))),obj(area(placing_area(paer3))),int(15,55)).
pickup(obj(kitchen_ware(mug(mug1))),obj(area(placing_area(pael3))),int(15,52)).
putdown(obj(kitchen_ware(mug(mug1))),obj(area(placing_area(pawr1))),int(60,90)).

serve_coffee(obj(area(seating_area(sae1)),obj(furniture(table1))).
dis(obj(area(manipulation_area(man1))),obj(robot(trixi)),int(1,77)).
dis(obj(kitchen_ware(mug(mug1))),obj(area(manipulation_area(man1))),int(1,92)).
dis(obj(kitchen_ware(mug(mug1))),obj(area(manipulation_area(man1))),int(110,410)).
dis(obj(area(manipulation_area(mae3))),obj(robot(trixi)),int(1,13)).
dis(obj(area(manipulation_area(mae3))),obj(robot(trixi)),int(32,32)).
dis(obj(area(manipulation_area(mae3))),obj(robot(trixi)),int(36,410)).
dis(obj(kitchen_ware(mug(mug1))),obj(robot(trixi)),int(1,410)).
con(obj(area(manipulation_area(man1))),obj(robot(trixi)),int(78,410)).
con(obj(kitchen_ware(mug(mug1))),obj(area(manipulation_area(man1))),int(93,109)).
con(obj(area(manipulation_area(mae3))),obj(robot(trixi)),int(14,31)).
con(obj(area(manipulation_area(mae3))),obj(robot(trixi)),int(33,35)).
pickup(obj(kitchen_ware(mug(mug1))),obj(area(placing_area(pael3))),int(15,50)).
pickup(obj(kitchen_ware(mug(mug1))),obj(area(placing_area(paer3))),int(15,53)).
putdown(obj(kitchen_ware(mug(mug1))),obj(area(placing_area(paer1))),int(100,130)).

