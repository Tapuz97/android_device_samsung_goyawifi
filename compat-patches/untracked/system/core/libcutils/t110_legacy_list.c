/* SPDX-License-Identifier: Apache-2.0 */
/* Preserve stock ANI7 audio HAL's exported C list API using the real platform operations. */
#if defined(T110_MRVL_LEGACY)
#define list_init t110_inline_list_init
#define list_add_tail t110_inline_list_add_tail
#define list_remove t110_inline_list_remove
#include <cutils/list.h>
#undef list_init
#undef list_add_tail
#undef list_remove

__attribute__((visibility("default"))) void list_init(struct listnode *node)
{
    t110_inline_list_init(node);
}

__attribute__((visibility("default"))) void list_add_tail(struct listnode *head, struct listnode *item)
{
    t110_inline_list_add_tail(head, item);
}

__attribute__((visibility("default"))) void list_remove(struct listnode *item)
{
    t110_inline_list_remove(item);
}
#endif
