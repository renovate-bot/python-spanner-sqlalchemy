# Copyright 2025 Google LLC All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from sample_helper import run_sample
from model import Venue


# Shows how to use an IDENTITY column for primary key generation. IDENTITY
# columns use a backing bit-reversed sequence to generate unique values that are
# safe to use for primary keys in Spanner.
#
# IDENTITY columns are used by default by the Spanner SQLAlchemy dialect for
# standard primary key columns.
#
# id: Mapped[int] = mapped_column(primary_key=True)
#
# This leads to the following table definition:
#
# CREATE TABLE ticket_sales (
# 	id INT64 NOT NULL GENERATED BY DEFAULT AS IDENTITY (BIT_REVERSED_POSITIVE),
#   ...
# ) PRIMARY KEY (id)
def auto_generated_primary_key_sample():
    engine = create_engine(
        "spanner:///projects/sample-project/"
        "instances/sample-instance/"
        "databases/sample-database",
        echo=True,
    )

    # Add a line like the following to use AUTO_INCREMENT instead of IDENTITY
    # when creating tables in SQLAlchemy.
    # https://cloud.google.com/spanner/docs/primary-key-default-value#serial-auto-increment

    # engine.dialect.use_auto_increment = True
    # Base.metadata.create_all(engine)

    with Session(engine) as session:
        # Venue automatically generates a primary key value using an IDENTITY
        # column. We therefore do not need to specify a primary key value when
        # we create an instance of Venue.
        venue = Venue(code="CH", name="Concert Hall", active=True)
        session.add_all([venue])
        session.commit()

        print("Inserted a venue with ID %d" % venue.id)


if __name__ == "__main__":
    run_sample(auto_generated_primary_key_sample)
