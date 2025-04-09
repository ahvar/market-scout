import os
os.environ['DATABASE_URL'] = 'sqlite://'

from datetime import datetime, timezone, timedelta
import unittest
from src.app import app, db
from src.app.models.researcher import Researcher
from src.app.models.profit_and_loss import ProfitAndLoss
from src.app.models.trade import Trade

class TestResearcherModel(unittest.TestCase):
    def setUp(self):
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_password_hashing(self):
        susan = Researcher(researcher_name='susan', email='susan@example.com')
        susan.set_password('cat')
        self.assertFalse(susan.check_password('dog'))
        self.assertTrue(susan.check_password('cat'))

    def test_avatar(self):
        john = Researcher(researcher_name='john', email='john@example.com')
    
    def test_pandl_construction(self):
        tim = Researcher(researcher_name='tim', email='tim@example.com')
        db.session.add(tim)
        db.session.commit()
        # Construct new pandl and verify the new PnL appears in tim's pandl relationship
        pnl = ProfitAndLoss(name='Tim PnL', researcher_id=Researcher.id)
        db.session.add(pnl)
        db.session.commit()
        self.assertEqual(len(tim.pandl), 1)
        self.assertEqual(tim.pand[0].name, 'Tim PnL')
        # Construct new Trade, add to pandl, and confirm trade is in PnL's trades relationship
        trade = Trade(open_price=100.00, profit_and_loss_id=pnl.id)
        db.session.add(trade)
        db.session.commit()
        self.assertEqual(len(pnl.trades), 1)
        self.assertEqual(pnl.trades[0].open_price, 100.00)


    def test_follow(self):
        john = Researcher(researcher_name='john', email='john@example.com')
        susan = Researcher(researcher_name='susan', email='susan@example.com')
        db.session.add(john)
        db.session.add(susan)
        db.session.commit()
        following = db.session.scalars(john.following.select()).all()
        followers = db.session.scalars(susan.followers.select()).all()
        self.assertEqual(following, [])
        self.assertEqual(followers, [])

        john.follow(susan)
        db.session.commit()
        self.assertTrue(john.is_following(susan))
        self.assertEqual(john.following_count(), 1)
        self.assertEqual(susan.followers_count(), 1)
        john_following = db.session.scalars(john.following.select()).all()
        susan_followers = db.session.scalars(susan.followers.select()).all()

        john.unfollow(susan)
        db.session.commit()
        self.assertFalse(john.is_following(susan))
        self.assertEqual(john.following_count(), 0)
        self.assertEqual(susan.followers_count(), 0)

    def test_following_profitability(self):
        # create four researchers: john, susan, david, mary
        john = Researcher(researcher_name='john', email='john@example.com')
        susan = Researcher(researcher_name='susan', email='susan@example.com')
        david = Researcher(researcher_name='david', email='david@example.com')
        mary = Researcher(researcher_name='mary', email='mary@example.com')

        db.session.add_all([john, susan, david, mary])
        db.session.commit()

        # create pandl for researchers
        pnl_john = ProfitAndLoss(name='John PnL', researcher_id=john.id)
        pnl_susan = ProfitAndLoss(name='Susan PnL', researcher_id=susan.id)
        pnl_david = ProfitAndLoss(name='David PnL', researcher_id=david.id)
        pnl_mary = ProfitAndLoss(name='Mary PnL', researcher_id=mary.id)

        db.session.add_all([pnl_john, pnl_susan, pnl_david, pnl_mary])
        db.session.commit()

        # create trades (opened/closed within the last 3 months) and add to each researcher’s PnL
        recent_open_date = datetime.now(timezone.utc) - timedelta(days=30)
        recent_close_date = datetime.now(timezone.utc)

        t_john = Trade(open_price=100, close_price=110, open_date=recent_open_date,
                        close_date=recent_close_date, profit_and_loss_id=pnl_john.id)
        t_susan = Trade(open_price=200, close_price=210, open_date=recent_open_date,
                        close_date=recent_close_date, profit_and_loss_id=pnl_susan.id)
        t_david = Trade(open_price=300, close_price=310, open_date=recent_open_date,
                        close_date=recent_close_date, profit_and_loss_id=pnl_david.id)
        t_mary = Trade(open_price=400, close_price=390, open_date=recent_open_date,
                        close_date=recent_close_date, profit_and_loss_id=pnl_mary.id)

        db.session.add_all([t_john, t_susan, t_david, t_mary])
        db.session.commit()

        # setup followers: john follows susan & david; susan follows mary; mary follows david
        john.follow(susan)
        john.follow(david)
        susan.follow(mary)
        mary.follow(david)
        db.session.commit()

        # check the following trades for each researcher through following_profitability()
        # Example: John should see Susan & David’s trades in the last 3 months
        john_results = john.following_profitability()
        self.assertTrue(any(row[1] == 'susan' for row in john_results))
        self.assertTrue(any(row[1] == 'david' for row in john_results))

        # Susan should see Mary’s PnL
        susan_results = susan.following_profitability()
        self.assertTrue(any(row[1] == 'mary' for row in susan_results))

        # Mary should see David’s PnL
        mary_results = mary.following_profitability()
        self.assertTrue(any(row[1] == 'david' for row in mary_results))

        # David follows nobody, so no results
        david_results = david.following_profitability()
        self.assertTrue(any(row[1] for row in david_results))
    

