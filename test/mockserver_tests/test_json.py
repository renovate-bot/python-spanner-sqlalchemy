# Copyright 2024 Google LLC All rights reserved.
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

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.testing import eq_, is_instance_of
from google.cloud.spanner_v1 import (
    FixedSizePool,
    ResultSet,
    BatchCreateSessionsRequest,
    ExecuteSqlRequest,
    CommitRequest,
    BeginTransactionRequest,
    TypeCode,
    JsonObject,
)
from test.mockserver_tests.mock_server_test_base import (
    MockServerTestBase,
    add_result,
    add_update_count,
)
from google.cloud.spanner_admin_database_v1 import UpdateDatabaseDdlRequest
import google.cloud.spanner_v1.types.type as spanner_type
import google.cloud.spanner_v1.types.result_set as result_set


class TestJson(MockServerTestBase):
    def test_create_table(self):
        from test.mockserver_tests.json_model import Base

        add_result(
            """SELECT true
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA="" AND TABLE_NAME="venues"
LIMIT 1
""",
            ResultSet(),
        )
        engine = create_engine(
            "spanner:///projects/p/instances/i/databases/d",
            connect_args={"client": self.client, "pool": FixedSizePool(size=10)},
        )
        Base.metadata.create_all(engine)
        requests = self.database_admin_service.requests
        eq_(1, len(requests))
        is_instance_of(requests[0], UpdateDatabaseDdlRequest)
        eq_(1, len(requests[0].statements))
        eq_(
            "CREATE TABLE venues (\n"
            "\tid INT64 NOT NULL, \n"
            "\tname STRING(MAX) NOT NULL, \n"
            "\tdescription JSON\n"
            ") PRIMARY KEY (id)",
            requests[0].statements[0],
        )

    def test_insert_dict(self):
        self._test_insert_json(
            {"type": "Stadium", "size": "Great"}, '{"size":"Great","type":"Stadium"}'
        )

    def test_insert_array(self):
        self._test_insert_json(
            [{"type": "Stadium", "size": "Great"}],
            '[{"size":"Great","type":"Stadium"}]',
        )

    def _test_insert_json(self, description, expected):
        from test.mockserver_tests.json_model import Venue

        add_update_count(
            "INSERT INTO venues (id, name, description) VALUES (@a0, @a1, @a2)", 1
        )
        engine = create_engine(
            "spanner:///projects/p/instances/i/databases/d",
            connect_args={"client": self.client, "pool": FixedSizePool(size=10)},
        )

        with Session(engine) as session:
            venue = Venue(id=1, name="Test", description=description)
            session.add(venue)
            session.commit()

        # Verify the requests that we got.
        requests = self.spanner_service.requests
        eq_(4, len(requests))
        is_instance_of(requests[0], BatchCreateSessionsRequest)
        is_instance_of(requests[1], BeginTransactionRequest)
        is_instance_of(requests[2], ExecuteSqlRequest)
        is_instance_of(requests[3], CommitRequest)
        request: ExecuteSqlRequest = requests[2]
        eq_(3, len(request.params))
        eq_("1", request.params["a0"])
        eq_("Test", request.params["a1"])
        eq_(expected, request.params["a2"])
        eq_(TypeCode.INT64, request.param_types["a0"].code)
        eq_(TypeCode.STRING, request.param_types["a1"].code)
        eq_(TypeCode.JSON, request.param_types["a2"].code)

    def test_select_dict(self):
        self._test_select_json(
            '{"size":"Great","type":"Stadium"}',
            JsonObject({"size": "Great", "type": "Stadium"}),
        )

    def test_select_array(self):
        self._test_select_json(
            '[{"size":"Great","type":"Stadium"}]',
            JsonObject([{"size": "Great", "type": "Stadium"}]),
        )

    def _test_select_json(self, description, expected):
        from test.mockserver_tests.json_model import Venue

        sql = "SELECT venues.id, venues.name, venues.description \n" "FROM venues"
        add_venue_query_result(sql, description)
        engine = create_engine(
            "spanner:///projects/p/instances/i/databases/d",
            connect_args={"client": self.client, "pool": FixedSizePool(size=10)},
        )

        with Session(engine.execution_options(read_only=True)) as session:
            venue = session.execute(select(Venue)).first()[0]
            eq_(venue.description, expected)


def add_venue_query_result(sql: str, description: str):
    result = result_set.ResultSet(
        dict(
            metadata=result_set.ResultSetMetadata(
                dict(
                    row_type=spanner_type.StructType(
                        dict(
                            fields=[
                                spanner_type.StructType.Field(
                                    dict(
                                        name="id",
                                        type=spanner_type.Type(
                                            dict(code=spanner_type.TypeCode.INT64)
                                        ),
                                    )
                                ),
                                spanner_type.StructType.Field(
                                    dict(
                                        name="name",
                                        type=spanner_type.Type(
                                            dict(code=spanner_type.TypeCode.STRING)
                                        ),
                                    )
                                ),
                                spanner_type.StructType.Field(
                                    dict(
                                        name="description",
                                        type=spanner_type.Type(
                                            dict(code=spanner_type.TypeCode.JSON)
                                        ),
                                    )
                                ),
                            ]
                        )
                    )
                )
            ),
        )
    )
    result.rows.extend(
        [
            (
                "1",
                "Test",
                description,
            ),
        ]
    )
    add_result(sql, result)