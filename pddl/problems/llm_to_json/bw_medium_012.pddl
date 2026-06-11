(define (problem bw_medium_012)
  (:domain blocks-world)

  (:objects
    a b c d - block
  )

  (:init
    (on_table a)
    (on_table d)
    (on c a)
    (on b d)
    (clear c)
    (clear b)
    (handempty)
  )

  (:goal
    (on a b)
  )
)
