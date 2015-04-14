
create table user (
  user_id integer primary key autoincrement,
  username text not null,
  email text not null,
  pw_hash text not null
);

create table follower (
  who_id integer,
  whom_id integer
);

create table message (
  message_id integer primary key autoincrement,
  author_id integer not null,
  text text not null,
  pub_date integer
);


create table access_token (
  user_id integer not null,
  access_token_text text not null
);

create table completed_deliveries (
	flower_order text not null,
	shipping_address text not null,
	total_cost real not null,
	driver_name text not null,
	estimated_delivery_time integer not null,
	reputation text not null,
	charge real not null,
	arrival_estimation text not null,
	picked_up_time text not null,
	actual_arrival_time text not null
);

create table deliveries_in_progress (
	flower_order text not null,
	shipping_address text not null,
	total_cost real not null,
	driver_name text not null,
	estimated_delivery_time integer not null,
	reputation text not null,
	charge real not null,
	arrival_estimation text not null,
	picked_up_time text not null
);

create table deliveries_awaiting_pickup (
	flower_order text not null,
	shipping_address text not null,
	total_cost real not null,
	driver_name text not null,
	estimated_delivery_time integer not null,
	reputation text not null,
	charge real not null,
	arrival_estimation text not null
);

create table deliveries_waiting_for_bids (
	order_id integer not null,
	flower_order text not null,
	shipping_address text not null,
	total_cost real not null
);
