DROP TABLE potions_catalog;

create table
  public.potions_catalog (
    sku text not null,
    created_at timestamp with time zone not null default now(),
    price integer not null default 0,
    constraint potions_catalog_pkey primary key (sku)
  ) tablespace pg_default;

-- Insert the initial rows
INSERT INTO public.potions_catalog (sku, quantity, price)
VALUES ('50_50_0_0', 1),
    ('0_50_50_0', 1),
    ('50_0_50_0', 1),
    ('100_0_0_0', 50),
    ('0_100_0_0', 50),

create table
  public.potions_inventory (
    sku text not null,
    created_at timestamp with time zone not null default now(),
    quantity integer not null default 0,
    constraint potions_inventory_sku_fkey foreign key (sku) references potions_catalog (sku) on update cascade on delete cascade
  ) tablespace pg_default;

create table
  public.global_inventory (
    id integer generated by default as identity,
    created_at timestamp with time zone not null default now(),
    num_red_ml integer not null default 0,
    gold integer not null default 100,
    num_green_ml integer not null default 0,
    num_blue_ml integer not null default 0,
    num_dark_ml integer not null default 0,
    constraint global_inventory_pkey primary key (id)
  ) tablespace pg_default;
    
-- Insert the global_inventory
INSERT INTO public.global_inventory (num_red_ml, num_green_ml, num_blue_ml, num_dark_ml, gold)
VALUES (0, 0, 0, 0, 100)

create table
  public.cart (
    cart_id bigint generated by default as identity,
    created_at timestamp with time zone not null default now(),
    customer_name text not null,
    constraint cart_items_pkey primary key (cart_id)
  ) tablespace pg_default;

create table
  public.cart_items (
    cart_item_id bigint generated by default as identity,
    created_at timestamp with time zone not null default now(),
    quantity integer not null default 0,
    cart_id bigint not null,
    sku text not null,
    constraint cart_items_pkey1 primary key (cart_item_id),
    constraint cart_items_cart_item_id_key unique (cart_item_id),
    constraint cart_items_cart_id_fkey foreign key (cart_id) references cart (cart_id) on update cascade on delete cascade
  ) tablespace pg_default;

