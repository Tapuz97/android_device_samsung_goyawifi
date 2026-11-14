/* SPDX-License-Identifier: Apache-2.0 */
// These libcutils operations became inline. Export the real operations locally
// for the exact legacy audio blob, instead of replacing platform libcutils.
struct listnode { listnode* next; listnode* prev; };
extern "C" {
__attribute__((visibility("default"))) void list_init(listnode* head) {
    head->next=head;head->prev=head;
}
__attribute__((visibility("default"))) void list_add_tail(listnode* head,listnode* item) {
    item->next=head;item->prev=head->prev;head->prev->next=item;head->prev=item;
}
__attribute__((visibility("default"))) void list_remove(listnode* item) {
    item->prev->next=item->next;item->next->prev=item->prev;
}
}
#if defined(__arm__) && !defined(__LP64__)
static_assert(sizeof(listnode)==8,"ANI7 list layout");
#endif
