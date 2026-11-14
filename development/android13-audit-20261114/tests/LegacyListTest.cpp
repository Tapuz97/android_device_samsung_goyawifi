#include <cassert>
#include <cstdio>
struct listnode {listnode* next;listnode* prev;};
extern "C" void list_init(listnode*);
extern "C" void list_add_tail(listnode*,listnode*);
extern "C" void list_remove(listnode*);
int main(){
 listnode head,a,b;list_init(&head);
 assert(head.next==&head&&head.prev==&head);
 list_add_tail(&head,&a);list_add_tail(&head,&b);
 assert(head.next==&a&&a.next==&b&&b.next==&head&&head.prev==&b&&b.prev==&a);
 list_remove(&a);assert(head.next==&b&&b.prev==&head);
 list_remove(&b);assert(head.next==&head&&head.prev==&head);
 puts("PASS: ARM legacy list ABI initialization/append/remove");
}
