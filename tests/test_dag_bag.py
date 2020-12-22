from unittest import TestCase
from airflow.models import DagBag


class TestDagBag(TestCase):
    def setUp(self):
        self.dagbag = DagBag()

    def test_import_dags(self):
        self.assertFalse(
            len(self.dagbag.import_errors),
            'Failed to import DAGs. Details: {}'.format(
                self.dagbag.import_errors
            )
        )
    
    def test_queue_present(self):
        for dag_id, dag in self.dagbag.dags.iteritems():
            queue = dag.default_args.get('queue', None)
            msg = 'Queue not for DAG {id}'.format(id=dag_id)
            self.assertNotEqual(None, queue, msg)
